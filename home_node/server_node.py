from __future__ import annotations
import asyncio
from pathlib import Path
from identity import NodeIdentity
from known_nodes import KnownNodesStore
from transfer_store import TransferStore
from node_auth_network import NodeAuthNetworkServer, NodeAuthNetworkError
from transfer_network import TransferNetwork, TransferNetworkError
from network import retry_send
from transport import close

HOST='0.0.0.0'; PORT=8765
ROOT=Path(__file__).resolve().parent
HOME_NODE_DATA=ROOT/'home_node_data'
IDENTITY_DIR=HOME_NODE_DATA/'home_node_key'
NODE_DATA=HOME_NODE_DATA/'node_data'
SIMPLE_DATA=ROOT/'simple_data'
RETRY_WINDOW=80
RETRY_INTERVAL=15
SCAN_INTERVAL=80

class HomeNodeServer:
    def __init__(self,host=HOST,port=PORT):
        self.host=host; self.port=port
        self.identity=NodeIdentity(IDENTITY_DIR)
        self.known_nodes=KnownNodesStore(NODE_DATA/'known_nodes.json')
        self.store=TransferStore(SIMPLE_DATA,ttl_seconds=RETRY_WINDOW)
        self.transfer=TransferNetwork(self.identity.node_id)
        self.server=None; self._outgoing_task=None; self._busy=set()

    async def handle_client(self,reader,writer):
        peer=writer.get_extra_info('peername')
        try:
            auth=NodeAuthNetworkServer(self.identity)
            remote=await auth.authenticate(reader,writer)
            endpoint=self.known_nodes.get(remote.node_id)
            if endpoint is None:
                raise NodeAuthNetworkError(f'Unknown remote NodeID: {remote.node_id}')
            if endpoint.public_key is not None and endpoint.public_key != remote.public_key:
                raise NodeAuthNetworkError('Known public key does not match authenticated key')
            path=await self.transfer.receive_file(reader,writer,self.store.area_path('incoming'),expected_sender_node_id=remote.node_id)
            print(f'Incoming file from {remote.node_id}: {path.name}')
        except Exception as exc:
            print(f'Connection {peer} failed: {type(exc).__name__}: {exc}')
        finally: await close(writer)

    async def outgoing_loop(self):
        while True:
            try:
                for path in self.store.list_files('outgoing'):
                    if not self.store.is_fresh(path): path.unlink(missing_ok=True); continue
                    if path.name in self._busy: continue
                    self._busy.add(path.name)

                    try:
                        delivered = False
                        for endpoint in self.known_nodes.all():
                            if endpoint.node_id == self.identity.node_id:
                                continue
                            try:
                                await retry_send(self.identity, endpoint, path,RETRY_WINDOW, RETRY_INTERVAL)
                                print(f'Outgoing delivered to {endpoint.node_id}: {path.name}')
                                delivered = True
                            except Exception as exc:
                                print(f'Outgoing delivery failed {endpoint.node_id}: {type(exc).__name__}: {exc}')
                        if delivered: path.unlink(missing_ok=True)
                        print(f'Outgoing file removed after successful delivery: {path.name}')
                    finally: self._busy.discard(path.name)

                self.store.cleanup_expired('outgoing')
                self.store.cleanup_expired('to_phone')
            except Exception as exc: print(f'Outgoing scheduler error: {exc}')
            await asyncio.sleep(SCAN_INTERVAL)

    async def start(self):
        self.server=await asyncio.start_server(self.handle_client,self.host,self.port)
        self._outgoing_task=asyncio.create_task(self.outgoing_loop())
        print('='*60); print('HOME NODE SERVER'); print('='*60)
        print(f'Node ID: {self.identity.node_id}')
        print(f'Listening: {self.host}:{self.port}')
        print(f'Incoming: {self.store.area_path("incoming")}')
        print('Server is running. Press Ctrl+C to stop.')
        async with self.server: await self.server.serve_forever()

    async def stop(self):
        if self._outgoing_task: self._outgoing_task.cancel(); self._outgoing_task=None
        if self.server: self.server.close(); await self.server.wait_closed(); self.server=None

def main():
    server=HomeNodeServer()
    try: asyncio.run(server.start())
    except KeyboardInterrupt: print('\nServer stopped.')

if __name__=='__main__': main()
