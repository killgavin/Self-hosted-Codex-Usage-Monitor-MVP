"""Real device-code login-start validation through production boundaries."""

import asyncio
import os

from app.config import Settings
from app.codex.adapter import AdapterState, CodexAppServerAdapter
from app.codex.process import CodexProcess
from app.services.auth import AuthService, LoginState


def test_real_device_code_login_start(tmp_path, monkeypatch) -> None:
    executable = os.environ.get("REAL_CODEX_EXECUTABLE")
    if not executable:
        raise AssertionError("REAL_CODEX_EXECUTABLE is required")
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))

    async def scenario() -> None:
        process = CodexProcess(Settings(executable))
        adapter = CodexAppServerAdapter(process)
        service = AuthService(adapter)
        child = None
        try:
            await adapter.initialize()
            status = await service.start_login()
            child = process.process
            assert adapter.state is AdapterState.READY
            assert status.state is LoginState.PENDING
            assert status.login_id
            assert status.verification_url
            assert status.user_code
        finally:
            await adapter.shutdown()

        assert adapter.state is AdapterState.STOPPED
        assert process.process is None
        assert child is not None
        assert child.returncode is not None

    asyncio.run(scenario())
