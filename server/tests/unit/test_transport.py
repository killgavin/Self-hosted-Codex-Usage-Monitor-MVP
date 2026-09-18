"""Automated unit coverage for the basic JSONL transport boundary."""

import asyncio
import json
from typing import Any

import pytest

from app.codex.exceptions import ProcessCommunicationFailed
from app.codex.transport import CodexTransport


class FakeWriter:
    def __init__(self) -> None:
        self.writes: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.writes.append(data)

    async def drain(self) -> None:
        return None


class FakeReader:
    def __init__(self) -> None:
        self.lines: asyncio.Queue[bytes] = asyncio.Queue()

    async def readline(self) -> bytes:
        return await self.lines.get()


class FakeChild:
    def __init__(self) -> None:
        self.stdin = FakeWriter()
        self.stdout = FakeReader()


def test_request_serialization_and_response_correlation() -> None:
    async def scenario() -> None:
        child = FakeChild()
        transport = CodexTransport(child)
        request = asyncio.create_task(transport.request("account/read", {"include": True}))
        await asyncio.sleep(0)

        sent = json.loads(child.stdin.writes[0])
        assert sent == {"method": "account/read", "id": 1, "params": {"include": True}}
        await child.stdout.lines.put(b'{"id":1,"result":{"status":"ready"}}\n')
        assert await request == {"status": "ready"}
        await transport.close()

    asyncio.run(scenario())


def test_error_response_is_controlled() -> None:
    async def scenario() -> None:
        child = FakeChild()
        transport = CodexTransport(child)
        request = asyncio.create_task(transport.request("account/read"))
        await asyncio.sleep(0)
        await child.stdout.lines.put(b'{"id":1,"error":{"message":"private payload"}}\n')
        with pytest.raises(ProcessCommunicationFailed, match="response returned an error"):
            await request
        await transport.close()

    asyncio.run(scenario())


def test_close_fails_pending_request_safely() -> None:
    async def scenario() -> None:
        child = FakeChild()
        transport = CodexTransport(child)
        request = asyncio.create_task(transport.request("account/read"))
        await asyncio.sleep(0)
        await transport.close(timeout=0.1)
        with pytest.raises(ProcessCommunicationFailed, match="transport closed"):
            await request
        await transport.close(timeout=0.1)

    asyncio.run(scenario())
