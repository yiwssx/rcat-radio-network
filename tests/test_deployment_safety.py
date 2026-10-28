"""Regression tests for approval gates and portal scope (host-safe)."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CTL = ROOT / "scripts" / "radioctl.sh"
LEGACY = ROOT / "scripts" / "one_round.py"
NGINX = ROOT / "portal" / "nginx.conf"


class DeploymentSafetyTests(unittest.TestCase):
    def test_deploy_refuses_missing_operator_ack_before_docker(self):
        completed = subprocess.run(
            ["bash", str(CTL), "deploy", "10.123.12.34"],
            cwd=ROOT, capture_output=True, text=True, timeout=8
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("Deployment needs --ack-shared-host", completed.stderr)

    def test_legacy_deploy_cannot_bypass_gate(self):
        completed = subprocess.run(
            [sys.executable, str(LEGACY), "--mode", "deploy",
             "--bind-ip", "10.123.12.34", "--ack-shared-host"],
            cwd=ROOT, capture_output=True, text=True, timeout=8
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Legacy deploy is disabled", completed.stderr)

    def test_radioctl_requires_private_gate_records(self):
        text = CTL.read_text(encoding="utf-8")
        for required in (
            'RRN00=APPROVED', 'RRN01=APPROVED', 'RRN02=APPROVED',
            'SHARED_HOST_CHANGE=APPROVED', 'RRN_BIND_IP=$BIND_IP'
        ):
            self.assertIn(required, text)
        self.assertIn('  deploy) deploy "$@" ;;', text)
        self.assertIn("rrn-deploy-approval.txt", text)

    def test_verify_checks_listener_proxy_not_unproxied_icecast(self):
        text = CTL.read_text(encoding="utf-8")
        self.assertIn(
            '"http://$BIND_IP:8750/listen/rcat_radio/radio.mp3"',
            text
        )
        self.assertNotIn(
            '"http://$BIND_IP:8600/radio.mp3"',
            text
        )

    def test_nowplaying_proxy_does_not_expose_other_stations(self):
        config = NGINX.read_text(encoding="utf-8")
        self.assertIn("location = /api/nowplaying/rcat_radio {", config)
        self.assertNotIn("location ~ ^/api/nowplaying", config)
        self.assertIn("location /api/ {", config)
        self.assertIn("return 403;", config)


if __name__ == "__main__":
    unittest.main()
