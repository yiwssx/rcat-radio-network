"""Regression: radioctl verify must clean temp files without an unbound EXIT trap."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CTL = ROOT / "scripts" / "radioctl.sh"

# Run the real verify function with mock HTTP/Docker helpers, completely offline.
# Source the script in --help mode to load functions without host operations.
VERIFY_SCRIPT = r"""
set -Eeuo pipefail
source "$1" --help >/dev/null
REPORT_DIR="$2"
ENV_FILE="$REPORT_DIR/.env"
BIND_IP=10.10.1.100
SIMULATE_BAD_STREAM="$3"
printf 'RRN_BIND_IP=%s\n' "$BIND_IP" > "$ENV_FILE"
check_host() { :; }
http_code() {
  case "$1" in
    *:8700/*) printf '302' ;;
    *:8750/*) printf '200' ;;
    *) printf '200' ;;
  esac
}
curl() {
  case "$*" in
    *"/api/nowplaying/rcat_radio"*)
      local previous="" argument output=""
      for argument in "$@"; do
        if [[ "$previous" == "-o" ]]; then output="$argument"; break; fi
        previous="$argument"
      done
      [[ -n "$output" ]] || return 1
      printf '%s\n' '{"station":{"shortcode":"rcat_radio"},"is_online":true}' > "$output"
      ;;
    *"/listen/rcat_radio/radio.mp3"*)
      if [[ "$SIMULATE_BAD_STREAM" == "yes" ]]; then
        printf '200 text/plain 8\n'
      else
        printf '200 audio/mpeg 2048\n'
      fi
      ;;
    *) return 1 ;;
  esac
}
compare_persisted_baseline() { return 0; }
verify
"""


class VerifyCleanupTests(unittest.TestCase):
    def run_mock_verify(self, bad_stream):
        with tempfile.TemporaryDirectory() as directory:
            proc = subprocess.run(
                ["bash", "-c", VERIFY_SCRIPT, "bash", str(CTL), directory,
                 "yes" if bad_stream else "no"],
                cwd=ROOT, capture_output=True, text=True, timeout=20,
            )
            report = Path(directory, "last-result.txt")
            self.assertTrue(report.is_file(), proc.stdout + proc.stderr)
            self.assertNotIn("unbound variable", proc.stderr)
            self.assertEqual(list(Path(directory).glob("verify.*")), [],
                             "verification temp directory leaked")
            return proc, report.read_text(encoding="utf-8")

    def test_success_path_exits_zero_and_cleans_temp(self):
        proc, report = self.run_mock_verify(bad_stream=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PASS: 5 local stream clients", proc.stdout)
        self.assertIn("status=SMOKE_PASS_MANUAL_TESTS_PENDING", report)

    def test_failure_path_exits_two_and_cleans_temp(self):
        proc, report = self.run_mock_verify(bad_stream=True)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("status=STREAM_OR_REGRESSION_INCOMPLETE", report)


if __name__ == "__main__":
    unittest.main()
