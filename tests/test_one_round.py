import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import one_round

class OneRoundPilotTests(unittest.TestCase):
    def test_bind_rejects_unspecified_and_testnet(self):
        for value in ("0.0.0.0","203.0.113.4","169.254.1.2","8.8.8.8","not-an-ip","::"):
            with self.subTest(value=value):
                self.assertFalse(one_round.valid_bind(value))

    def test_bind_accepts_private_and_loopback(self):
        for value in ("10.123.45.67","172.16.8.8","192.168.1.9","127.0.0.1"):
            self.assertTrue(one_round.valid_bind(value))

    def test_baseline_regression(self):
        faults=one_round.compare_baseline(
            {"pdf_hub":200,"anyflip":200},{"pdf_hub":500,"anyflip":200},
            {"8081":True,"8094":True})
        self.assertEqual(len(faults),1)

    def test_unreachable_existing_service_is_blocker(self):
        faults=one_round.compare_baseline(
            {"pdf_hub":None,"anyflip":200},{"pdf_hub":None,"anyflip":200},
            {"8081":True,"8094":True})
        self.assertTrue(faults)

    def test_station_selection(self):
        xs=[{"station":{"shortcode":"another"}},{"station":{"shortcode":"rcat_radio"},"is_online":True}]
        self.assertEqual(one_round.extract_station(xs)["station"]["shortcode"],"rcat_radio")
        self.assertIsNone(one_round.extract_station([]))

    def test_generated_original_audio(self):
        import wave
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"tone.wav"
            one_round.create_test_audio(p)
            with wave.open(str(p),"rb") as wav:
                self.assertEqual((wav.getnchannels(),wav.getframerate(),wav.getnframes()),
                                 (1,22050,12*22050))
            n=p.stat().st_size
            one_round.create_test_audio(p)
            self.assertEqual(p.stat().st_size,n)

    def test_private_file_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/".env"
            self.assertTrue(one_round.write_private(p,"PASSWORD=random\n"))
            self.assertFalse(one_round.write_private(p,"PASSWORD=overwritten\n"))
            self.assertEqual(p.stat().st_mode & 0o777,0o600)

    def test_compose_isolation(self):
        source=(Path(__file__).resolve().parents[1]/"deployment"/"compose.pilot.yaml").read_text()
        self.assertNotIn("privileged:",source)
        self.assertNotIn("docker.sock",source)
        self.assertIn("127.0.0.1:8700:8700",source)
        self.assertIn("8750:80",source)

if __name__=="__main__":
    unittest.main()
