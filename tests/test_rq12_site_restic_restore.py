"""Pure selection and production-protection tests; no Restic and no real files."""
from __future__ import annotations

from datetime import date
import importlib.util
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location(
    "rq12_site_restic_restore", ROOT / "tools/rq12_site_restic_restore.py",
)
assert spec and spec.loader
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

ONE = "a" * 64
TWO = "b" * 64


class ResticRestoreSelectionTests(unittest.TestCase):
    def test_choose_exact_day_and_host_ha_snapshot(self):
        snapshots = [
            {"id": ONE, "time": "2026-11-09T02:37:11Z",
             "hostname": "weidnerhome-srv2",
             "paths": ["/srv/containers/homeassistant"]},
            {"id": TWO, "time": "2026-11-09T05:00:00Z",
             "hostname": "another-system",
             "paths": ["/srv/containers/homeassistant"]},
            {"id": "c"*64, "time": "2026-11-08T02:37:11Z",
             "hostname": "weidnerhome-srv2",
             "paths": ["/srv/containers/homeassistant"]},
        ]
        got = tool.choose_snapshot(
            snapshots, day=date(2026, 11, 9),
            ha_path="/srv/containers/homeassistant/config",
            host="weidnerhome-srv2", timezone="Europe/Vienna",
        )
        self.assertEqual(got["id"], ONE)

    def test_no_unqualified_latest_fallback(self):
        with self.assertRaises(tool.ResticRehearsalError):
            tool.choose_snapshot(
                [{"id": ONE, "time": "2026-11-09T03:37:11Z",
                  "hostname": "weidnerhome-srv2",
                  "paths": ["/srv/containers/dokuwiki"]}],
                day=date(2026, 11, 9),
                ha_path="/srv/containers/homeassistant/config",
                host="weidnerhome-srv2", timezone="Europe/Vienna",
            )

    def test_no_incorrect_snapshot_ids(self):
        with self.assertRaises(tool.ResticRehearsalError):
            tool.choose_snapshot(
                [{"id": "latest", "time": "2026-11-09T03:37:11Z",
                  "hostname": "weidnerhome-srv2",
                  "paths": ["/srv/containers/homeassistant"]}],
                day=date(2026, 11, 9),
                ha_path="/srv/containers/homeassistant/config",
                host="weidnerhome-srv2", timezone="Europe/Vienna",
            )

    def test_lab_never_points_into_live_config(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            live = base / "active"
            live.mkdir()
            (live / ".storage").mkdir()
            mounted = base / "remote"
            mounted.mkdir()
            repo = mounted / "repository"
            repo.mkdir()
            pw = base / "secret"
            pw.mkdir()
            (pw / "restic.pass").write_text("SECRET\n")
            protected = live / "bad_lab"
            with patch.object(tool.os, "geteuid", return_value=0), \
                 patch.object(tool.os.path, "ismount", return_value=True), \
                 patch.object(tool.shutil, "which", return_value="/usr/bin/restic"), \
                 patch.object(tool.shutil, "disk_usage",
                              return_value=type("Usage", (), {"free": 99*1024**3})()):
                with self.assertRaises(tool.ResticRehearsalError):
                    tool._guard(
                        repo=repo, mounted=mounted, password=pw/"restic.pass",
                        lab=protected, live=live,
                        ha_path="/srv/containers/homeassistant/config",
                        restic_bin="/usr/bin/restic",
                    )

    def test_refuses_missing_mount_before_reading_repo(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            live = base / "active"
            live.mkdir()
            (live / ".storage").mkdir()
            mount = base / "remote"
            mount.mkdir()
            repo = mount / "repository"
            repo.mkdir()
            pw = base / "secure"
            pw.mkdir()
            (pw / "p").write_text("fake")
            with patch.object(tool.os, "geteuid", return_value=0), \
                 patch.object(tool.os.path, "ismount", return_value=False):
                with self.assertRaises(tool.ResticRehearsalError):
                    tool._guard(
                        repo=repo, mounted=mount, password=pw/"p",
                        lab=base/"laboratory", live=live,
                        ha_path="/srv/containers/homeassistant/config",
                        restic_bin="/usr/bin/restic",
                    )


if __name__ == "__main__":
    unittest.main()
