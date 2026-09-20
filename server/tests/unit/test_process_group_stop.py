"""Deterministic process-group shutdown coverage."""

import asyncio
import os
import signal
import sys
import textwrap
from pathlib import Path

import pytest

from app.codex.process import CodexProcess
from app.config import Settings


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX semantics")
def test_stop_reaps_wrapper_and_descendant_in_owned_process_group(tmp_path: Path, monkeypatch) -> None:
    pid_file = tmp_path / "descendant.pid"
    wrapper = tmp_path / "wrapper.py"
    wrapper.write_text(
        textwrap.dedent(
            """
            #!/usr/bin/env python3
            import os
            import signal
            import subprocess
            import sys
            import time

            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
            with open(os.environ["DESCENDANT_PID_FILE"], "w", encoding="ascii") as pid_file:
                pid_file.write(str(child.pid))
                pid_file.flush()

            # Direct wrapper-only TERM is ignored; only an owned group signal
            # reaches the descendant, while the later group KILL ends wrapper.
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            while True:
                time.sleep(60)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    wrapper.chmod(0o700)

    async def scenario() -> None:
        monkeypatch.setenv("DESCENDANT_PID_FILE", str(pid_file))
        process = CodexProcess(Settings(str(wrapper)))
        child = await process.start()
        descendant_pid: int | None = None
        try:
            for _ in range(200):
                if pid_file.exists():
                    descendant_pid = int(pid_file.read_text(encoding="ascii"))
                    break
                await asyncio.sleep(0.01)
            assert descendant_pid is not None
            assert os.getpgid(child.pid) == child.pid
            os.kill(descendant_pid, 0)

            await process.stop()

            assert child.returncode is not None
            assert process.process is None
            for _ in range(200):
                try:
                    os.kill(descendant_pid, 0)
                except ProcessLookupError:
                    break
                await asyncio.sleep(0.01)
            else:
                raise AssertionError("descendant process still exists")
        finally:
            # Keep this cleanup direct and narrowly targeted so a regression
            # cannot signal the pytest process group.
            if process.process is not None:
                process.process.kill()
                await process.process.wait()
            if descendant_pid is not None:
                try:
                    os.kill(descendant_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    asyncio.run(scenario())
