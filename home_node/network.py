from __future__ import annotations
import asyncio
from transport import connect, close
from node_auth_network import NodeAuthNetworkClient
from transfer_network import TransferNetwork

class NetworkError(Exception): pass

async def send_to_node(identity, endpoint, source_path, timeout=10):
    reader=writer=None
    try:
        reader,writer=await connect(endpoint.host,endpoint.port,timeout=timeout)
        await NodeAuthNetworkClient(identity,endpoint.node_id).authenticate(reader,writer)
        return await TransferNetwork(identity.node_id).send_file(reader,writer,source_path,endpoint.node_id)
    finally:
        if writer is not None: await close(writer)

async def retry_send(identity, endpoint, source_path, duration=300, interval=15):
    deadline=asyncio.get_running_loop().time()+duration
    last=None
    while asyncio.get_running_loop().time() < deadline:
        try: return await send_to_node(identity,endpoint,source_path)
        except Exception as exc:
            last=exc; await asyncio.sleep(min(interval,max(0,deadline-asyncio.get_running_loop().time())))
    raise NetworkError(f'Could not deliver to {endpoint.node_id} within {duration}s') from last
