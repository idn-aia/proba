from __future__ import annotations
import asyncio
from framing import receive_json, send_json

class TransportError(Exception): pass

async def connect(host, port, ssl_context=None, timeout=10):
    try: return await asyncio.wait_for(asyncio.open_connection(host,port,ssl=ssl_context),timeout)
    except Exception as exc: raise TransportError(f'Connection failed to {host}:{port}') from exc

async def close(writer):
    writer.close()
    try: await writer.wait_closed()
    except Exception: pass

class JsonTransport:
    def __init__(self,reader,writer): self.reader=reader; self.writer=writer
    async def send(self,message): await send_json(self.writer,message)
    async def receive(self): return await receive_json(self.reader)
    async def close(self): await close(self.writer)
