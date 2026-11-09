"""Synthetic Red Queen 1.2 end-to-end scheduler staging on REAL HA imports.

The test runs within the isolated HA 2026.9.2 Docker container. Real
Home Assistant event-helper API signatures are imported; timers are patched
to deterministic synthetic callbacks. No real HA services or hardware exist.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import patch
import sys

sys.path.insert(0, "/config")
from custom_components.red_queen import smart_living_automation as scheduler_module
from custom_components.red_queen.smart_living_automation_logic import parse_automation_rules
from custom_components.red_queen.smart_living_logic import validate_light_request, exposed_modes


LIGHT = "light.dali_synthetic_aussen_rgbw"
OTHER = "light.dali_synthetic_wohnzimmer_rgbw"
MISSING = "light.dali_synthetic_removed_rgbw"
MOTION = "binary_sensor.synthetic_motion"


class Harness:
    def __init__(self):
        self.listeners = []
        self.tasks = []
        self.dispatches = []
        self.mode = "home"
        self.quiet_entity_id = "binary_sensor.synthetic_quiet"
        self.states = {
            LIGHT: SimpleNamespace(
                state="off", attributes={"supported_color_modes": ["rgbw"]}
            ),
            OTHER: SimpleNamespace(
                state="off", attributes={"supported_color_modes": ["rgbw"]}
            ),
            self.quiet_entity_id: SimpleNamespace(state="off", attributes={}),
        }
        self.hass = SimpleNamespace(
            states=SimpleNamespace(get=lambda entity_id:self.states.get(entity_id)),
            async_create_task=self.create_task,
        )
        self.rgbw_targets = {LIGHT:"Synthetic exterior", OTHER:"Synthetic lounge"}
        self.scenes = {
            "exterior": {"id":"exterior", "name":"Exterior", "lights":{
                LIGHT: {"state":"on", "attributes":{
                    "brightness":180, "rgbw_color":[0,0,0,200],
                }},
            }},
            "missing": {"id":"missing", "name":"Missing", "lights":{
                MISSING: {"state":"on", "attributes":{}},
            }},
        }
        self.rules = parse_automation_rules([
            {
                "id":"sun_on", "name":"Exterior sunset", "enabled":True,
                "scene_id":"exterior", "action":"on",
                "trigger":{"type":"sun","event":"sunset","offset_minutes":-10},
                "allowed_modes":["home","away","vacation"],"allow_quiet":True,
            },
            {
                "id":"clock_off", "name":"Exterior 23:00 OFF", "enabled":True,
                "scene_id":"exterior", "action":"off",
                "trigger":{"type":"time","at":"23:00"},
            },
            {
                "id":"motion_on", "name":"Movement on", "enabled":True,
                "scene_id":"exterior", "action":"on",
                "trigger":{"type":"state","entity_id":MOTION,"to":"on"},
            },
            {
                "id":"disabled", "name":"Disabled", "enabled":False,
                "scene_id":"exterior", "action":"on",
                "trigger":{"type":"time","at":"21:00"},
            },
            {
                "id":"missing_on", "name":"Missing source", "enabled":True,
                "scene_id":"missing", "action":"on",
                "trigger":{"type":"sun","event":"sunrise"},
            },
        ], self.scenes)

    @property
    def scene_targets(self):
        return self.rgbw_targets

    def validate_scene_light_request(self, entity_id, service, attributes, state):
        assert entity_id in self.scene_targets
        return (
            validate_light_request(
                exposed_modes(state.attributes.get("supported_color_modes")),
                attributes,
            ) if service == "turn_on" else {}
        )

    @property
    def quiet(self):
        return self.states[self.quiet_entity_id].state != "off"

    def create_task(self, coroutine, name=None):
        task = asyncio.create_task(coroutine, name=name)
        self.tasks.append(task)
        return task

    async def flush(self):
        tasks, self.tasks = self.tasks, []
        if tasks:
            await asyncio.gather(*tasks)

    async def async_light_dispatch(self, entity_id, service, params):
        if entity_id not in self.rgbw_targets:
            raise AssertionError("Non-allowlisted physical dispatch")
        self.dispatches.append((entity_id, service, dict(params)))
        self.states[entity_id].state = "on" if service=="turn_on" else "off"


class EventStubs:
    def __init__(self):
        self.listeners = []

    def attach(self, kind, callback, **details):
        item = SimpleNamespace(
            kind=kind, callback=callback, details=details, active=True,
        )
        self.listeners.append(item)
        def unsubscribe():
            item.active=False
        return unsubscribe

    def sunset(self,hass,callback,**kw):
        return self.attach("sunset",callback,**kw)

    def sunrise(self,hass,callback,**kw):
        return self.attach("sunrise",callback,**kw)

    def clock(self,hass,callback,**kw):
        return self.attach("time",callback,**kw)

    def state(self,hass,entities,callback):
        return self.attach("state",callback,entities=list(entities))

    def active(self,kind):
        return [item for item in self.listeners if item.active and item.kind==kind]

    def fire_clock(self,hour,minute):
        for listener in self.active("time"):
            if listener.details["hour"]==hour and listener.details["minute"]==minute:
                listener.callback(datetime.now(UTC))

    def fire_sun(self,kind):
        for listener in self.active(kind):
            listener.callback(datetime.now(UTC))

    def fire_state(self, entity_id,old,new):
        event=SimpleNamespace(data={
            "entity_id":entity_id,
            "old_state": None if old is None else SimpleNamespace(state=old),
            "new_state": None if new is None else SimpleNamespace(state=new),
        })
        for listener in self.active("state"):
            if entity_id in listener.details["entities"]:
                listener.callback(event)


async def main():
    h=Harness()
    trackers=EventStubs()
    with (patch.object(scheduler_module,"async_track_sunset",trackers.sunset),
          patch.object(scheduler_module,"async_track_sunrise",trackers.sunrise),
          patch.object(scheduler_module,"async_track_time_change",trackers.clock),
          patch.object(scheduler_module,"async_track_state_change_event",trackers.state)):
        scheduler=scheduler_module.SmartLightingScheduler(h.hass,h)
        scheduler.async_start(h.rules)
        assert len(scheduler._listeners)==3, scheduler.snapshot()
        assert "missing_on" in scheduler.snapshot()["blocked_rules"]
        assert not h.dispatches, "Startup must never send commands"
        assert not trackers.active("sunrise"), "Unavailable target listener registered"
        assert len(trackers.active("sunset"))==1
        assert len(trackers.active("time"))==1
        assert len(trackers.active("state"))==1
        assert trackers.active("sunset")[0].details["offset"].total_seconds()==-600

        # Sunset in holiday mode may switch on only the configured exterior.
        h.mode="vacation"
        trackers.fire_sun("sunset")
        await h.flush()
        assert h.dispatches==[(
            LIGHT,"turn_on",{"brightness":180,"rgbw_color":(0,0,0,200)},
        )], h.dispatches
        assert h.states[OTHER].state=="off"

        # Sunset ON during known quiet mode allowed only by explicit rule opt-in.
        h.states[h.quiet_entity_id].state="on"
        trackers.fire_sun("sunset")
        await h.flush()
        assert len(h.dispatches)==2, h.dispatches

        # A missing quiet sensor cannot authorize a scheduled ON.
        h.states[h.quiet_entity_id].state="unavailable"
        trackers.fire_sun("sunset")
        await h.flush()
        assert len(h.dispatches)==2
        assert scheduler.snapshot()["recent"][-1]["reason"]=="quiet_sensor_unavailable"

        # OFF at 23:00 is permitted even in vacation/quiet/unavailable.
        trackers.fire_clock(23,0)
        await h.flush()
        assert len(h.dispatches)==3
        assert h.dispatches[-1]==(LIGHT,"turn_off",{})
        assert h.states[OTHER].state=="off"

        # State triggers ignore restore, unavailability, and unrelated entities.
        h.mode="home"
        h.states[h.quiet_entity_id].state="off"
        trackers.fire_state(MOTION,None,"on")
        trackers.fire_state(MOTION,"unavailable","on")
        trackers.fire_state("binary_sensor.other","off","on")
        await h.flush()
        assert len(h.dispatches)==3
        trackers.fire_state(MOTION,"off","on")
        await h.flush()
        assert len(h.dispatches)==4
        assert h.dispatches[-1][1]=="turn_on"

        # An absent/missing source is skipped without taking down the scheduler.
        blocked=await scheduler.async_fire("missing_on")
        assert blocked["status"]=="suppressed" and len(h.dispatches)==4
        disabled = await scheduler.async_fire("disabled")
        assert disabled["status"]=="suppressed"
        assert disabled["reason"]=="rule_disabled"
        assert len(h.dispatches)==4

        # Unsubscribe on unload: stale event callbacks cannot switch lights.
        scheduler.async_stop()
        assert all(not listener.active for listener in trackers.listeners)
        previous=len(h.dispatches)
        trackers.fire_sun("sunset")
        trackers.fire_clock(23,0)
        await h.flush()
        assert len(h.dispatches)==previous

        # After reload there is exactly one set of new listeners.
        scheduler2=scheduler_module.SmartLightingScheduler(h.hass,h)
        scheduler2.async_start(h.rules)
        assert len(trackers.active("sunset"))==1
        assert len(trackers.active("time"))==1
        assert len(trackers.active("state"))==1
        assert not h.tasks
        scheduler2.async_stop()
        print("PASS: HA imports: 3 listeners + 1 safely suspended rule")
        print("PASS: sunset offset, targeted ON and OFF, time at 23:00")
        print("PASS: vacation and known quiet opt-in; unavailable quiet fail closed")
        print("PASS: no startup commands; synthetic movement only on real off->on")
        print("PASS: unload/reload removes and rebinds listeners with no replay")
        print("PASS: no real lights, PLC, Sonos, integrations or network required")


if __name__=="__main__":
    asyncio.run(main())
