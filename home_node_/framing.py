"""Length-prefixed network framing."""
from __future__ import annotations
import asyncio, struct
from protocol import MAX_FRAME_SIZE

class FrameError(Exception): pass

async def send_frame(writer: asyncio.StreamWriter, data: bytes) -> None:
    if not isinstance(data, bytes): raise TypeError("data must be bytes")
    if len(data) > MAX_FRAME_SIZE: raise FrameError("frame too large")
    writer.write(struct.pack(">I", len(data)) + data)
    await writer.drain()

async def receive_frame(reader: asyncio.StreamReader) -> bytes:
    try:
        header = await reader.readexactly(4)
    except asyncio.IncompleteReadError as exc:
        raise FrameError("Connection closed while reading frame header") from exc
    length = struct.unpack(">I", header)[0]
    if length > MAX_FRAME_SIZE: raise FrameError("frame too large")
    try:
        return await reader.readexactly(length)
    except asyncio.IncompleteReadError as exc:
        raise FrameError("Connection closed while reading frame payload") from exc

async def send_json(writer, message: dict) -> None:
    from protocol import dumps_message
    await send_frame(writer, dumps_message(message))

async def receive_json(reader) -> dict:
    from protocol import loads_message
    return loads_message(await receive_frame(reader))
