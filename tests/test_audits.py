import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import preflight
import compose_audit

class AuditTests(unittest.TestCase):
    def test_listening_ports(self):
        self.assertEqual(preflight.listening_ports("tcp LISTEN 0 1 0.0.0.0:8700 0.0.0.0:*"), {8700})
    def test_docker_port(self):
        sample=json.dumps({"Ports":"0.0.0.0:8094->8094/tcp, [::]:8094->8094/tcp"})
        self.assertEqual(preflight.published_ports(sample), {8094})
    def test_protected_port(self):
        cfg={"services":{"radio":{"ports":[{"host_ip":"127.0.0.1","published":"8081","target":80}]}}}
        self.assertTrue(compose_audit.check(cfg))
    def test_public_binding(self):
        cfg={"services":{"radio":{"ports":[{"published":"8700","target":80}]}}}
        self.assertTrue(compose_audit.check(cfg))
    def test_unapproved_specific_bind(self):
        cfg={"services":{"radio":{"ports":[{"host_ip":"203.0.113.4","published":"8700","target":80}]}}}
        self.assertTrue(any("unapproved host binding" in x for x in compose_audit.check(cfg)))
    def test_privileged(self):
        self.assertTrue(compose_audit.check({"services":{"radio":{"privileged":True}}}))
    def test_allowed_local_port(self):
        cfg={"services":{"radio":{"ports":[{"host_ip":"127.0.0.1","published":"8700","target":80}]}}}
        self.assertEqual(compose_audit.check(cfg), [])
    def test_docker_socket(self):
        cfg={"services":{"radio":{"volumes":["/var/run/docker.sock:/var/run/docker.sock"]}}}
        self.assertTrue(compose_audit.check(cfg))
    def test_range_collision(self):
        cfg={"services":{"radio":{"ports":[{"host_ip":"127.0.0.1","published":"8000-8500","target":"8000-8500"}]}}}
        self.assertTrue(compose_audit.check(cfg))

if __name__ == "__main__":
    unittest.main()
