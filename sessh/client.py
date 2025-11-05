"""Sessh client implementation using subprocess."""
import json
import subprocess
import os
from typing import Optional, Dict, Any


class SesshClient:
    """Client for managing persistent SSH sessions via sessh CLI."""

    def __init__(
        self,
        alias: str,
        host: str,
        port: Optional[int] = None,
        sessh_bin: Optional[str] = None,
        identity: Optional[str] = None,
        proxyjump: Optional[str] = None,
    ):
        """
        Initialize a sessh client.

        Args:
            alias: Session alias name
            host: SSH host (user@host)
            port: SSH port (default: 22)
            sessh_bin: Path to sessh binary (default: "sessh" from PATH)
            identity: Path to SSH private key
            proxyjump: ProxyJump host (e.g., "bastionuser@bastion")
        """
        self.alias = alias
        self.host = host
        self.port = port
        self.sessh_bin = sessh_bin or "sessh"
        self.identity = identity
        self.proxyjump = proxyjump

    def _run_sessh(
        self, cmd: str, *args: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Run sessh command and return JSON response."""
        env = os.environ.copy()
        env["SESSH_JSON"] = "1"
        if self.identity:
            env["SESSH_IDENTITY"] = self.identity
        if self.proxyjump:
            env["SESSH_PROXYJUMP"] = self.proxyjump

        sessh_args = [self.sessh_bin, cmd, self.alias, self.host]
        if self.port:
            sessh_args.append(str(self.port))
        sessh_args.extend(args)

        result = subprocess.run(
            sessh_args,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

        if result.returncode != 0 and not result.stdout:
            raise RuntimeError(
                f"sessh {cmd} failed: {result.stderr or f'exit code {result.returncode}'}"
            )

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON from sessh: {result.stdout}")

    def open(self) -> Dict[str, Any]:
        """Open or ensure a persistent remote tmux session."""
        return self._run_sessh("open")

    def run(self, command: str) -> Dict[str, Any]:
        """
        Send a command into the persistent tmux session.

        Args:
            command: Command string to execute
        """
        return self._run_sessh("run", "--", command)

    def logs(self, lines: int = 300) -> Dict[str, Any]:
        """
        Capture recent output from the tmux session.

        Args:
            lines: Number of lines to capture (default: 300)
        """
        return self._run_sessh("logs", str(lines))

    def status(self) -> Dict[str, Any]:
        """Check whether the SSH controlmaster and tmux session exist."""
        return self._run_sessh("status")

    def close(self) -> Dict[str, Any]:
        """Kill tmux session and close the controlmaster."""
        return self._run_sessh("close")

    def attach(self) -> None:
        """
        Attach to the tmux session interactively.

        Note: This will block and take over the terminal.
        """
        env = os.environ.copy()
        if self.identity:
            env["SESSH_IDENTITY"] = self.identity
        if self.proxyjump:
            env["SESSH_PROXYJUMP"] = self.proxyjump

        sessh_args = [self.sessh_bin, "attach", self.alias, self.host]
        if self.port:
            sessh_args.append(str(self.port))

        # For attach, we want interactive mode, so use subprocess.run without capture_output
        subprocess.run(sessh_args, env=env, check=False)

