"""Tests for sessh client (requires sessh binary and SSH setup)."""
import unittest
from unittest.mock import patch, MagicMock
from sessh.client import SesshClient


class TestSesshClient(unittest.TestCase):
    """Test SesshClient methods."""

    def setUp(self):
        """Set up test client."""
        self.client = SesshClient("test", "user@example.com")

    @patch("subprocess.run")
    def test_open(self, mock_run):
        """Test open command."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"ok":true,"op":"open"}', stderr=""
        )
        result = self.client.open()
        self.assertEqual(result["op"], "open")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run(self, mock_run):
        """Test run command."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"ok":true,"op":"run"}', stderr=""
        )
        result = self.client.run("echo hello")
        self.assertEqual(result["op"], "run")
        args = mock_run.call_args[0][0]
        self.assertIn("--", args)
        self.assertIn("echo hello", args)

    @patch("subprocess.run")
    def test_logs(self, mock_run):
        """Test logs command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"ok":true,"op":"logs","output":"test output"}',
            stderr="",
        )
        result = self.client.logs(100)
        self.assertEqual(result["op"], "logs")
        args = mock_run.call_args[0][0]
        self.assertIn("100", args)

    @patch("subprocess.run")
    def test_status(self, mock_run):
        """Test status command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"ok":true,"op":"status","master":1,"session":1}',
            stderr="",
        )
        result = self.client.status()
        self.assertEqual(result["op"], "status")
        self.assertEqual(result["master"], 1)

    @patch("subprocess.run")
    def test_close(self, mock_run):
        """Test close command."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"ok":true,"op":"close"}', stderr=""
        )
        result = self.client.close()
        self.assertEqual(result["op"], "close")


if __name__ == "__main__":
    unittest.main()

