# RC7 Sonos native-announce hotfix

This patch replaces the redundant Sonos snapshot/wait/restore playback path with
the live-verified Home Assistant Sonos native announce overlay:

- `media_player.play_media`
- TTS Media Source URL
- `announce: true`
- announcement volume through `extra.volume`
- no Red Queen Sonos snapshot or restore command

Replace:

```text
/config/custom_components/wnhf/providers/notifications.py
```

with the packaged file at:

```text
custom_components/wnhf/providers/notifications.py
```

Restart Home Assistant afterward. Repeat the Office `notifications.announce` live
test while music is playing. Music must resume once without the earlier second
interruption.
