from __future__ import annotations
from pathlib import Path
from transfer import make_transfer_meta, TransferMeta, TransferError
from transfer_chunks import iter_file_chunks
from framing import send_json, receive_json
from protocol import *

class TransferNetworkError(Exception): pass

class TransferNetwork:
    def __init__(self, local_node_id, chunk_size=CHUNK_SIZE): self.local_node_id=local_node_id; self.chunk_size=chunk_size

    async def send_file(self, reader, writer, source_path, recipient_node_id):
        if recipient_node_id == self.local_node_id: raise ValueError('Recipient must be remote node')
        meta=make_transfer_meta(source_path,self.local_node_id,recipient_node_id)
        await send_json(writer,{"type":TRANSFER_OFFER,"meta":meta.to_dict()})
        answer=await receive_json(reader)
        if answer.get('type') != TRANSFER_ACCEPT or answer.get('transfer_id') != meta.transfer_id: raise TransferNetworkError('Transfer was not accepted')
        for index,data in iter_file_chunks(source_path,self.chunk_size):
            await send_json(writer,{"type":TRANSFER_CHUNK,"transfer_id":meta.transfer_id,"index":index,"data":encode_bytes(data)})
        await send_json(writer,{"type":TRANSFER_COMPLETE,"transfer_id":meta.transfer_id,"sha256":meta.sha256})
        ack=await receive_json(reader)
        if ack.get('type') != TRANSFER_ACK or not ack.get('ok'): raise TransferNetworkError('Transfer acknowledgement failed')
        return meta

    async def receive_file(self, reader, writer, output_directory, expected_sender_node_id=None):
        offer=await receive_json(reader)
        if offer.get('type') != TRANSFER_OFFER: raise TransferNetworkError('Expected transfer offer')
        meta=TransferMeta.from_dict(offer['meta'])
        if meta.recipient_node_id != self.local_node_id: raise TransferNetworkError('Transfer recipient does not match local node')
        if expected_sender_node_id and meta.sender_node_id != expected_sender_node_id: raise TransferNetworkError('Transfer sender does not match authenticated node')
        out=Path(output_directory); out.mkdir(parents=True,exist_ok=True)
        safe_name=Path(meta.filename).name
        if not safe_name or safe_name in ('.','..'): raise TransferNetworkError('Invalid filename')
        temp=out/(f'.{meta.transfer_id}.part')
        final=out/safe_name
        await send_json(writer,{"type":TRANSFER_ACCEPT,"transfer_id":meta.transfer_id})
        import hashlib
        h=hashlib.sha256(); received=0; expected_index=0
        with temp.open('wb') as f:
            while True:
                msg=await receive_json(reader)
                if msg.get('transfer_id') != meta.transfer_id: raise TransferNetworkError('Transfer ID mismatch')
                if msg.get('type') == TRANSFER_CHUNK:
                    if int(msg['index']) != expected_index: raise TransferNetworkError('Chunk order mismatch')
                    data=decode_bytes(msg['data']); received+=len(data)
                    if received>meta.size: raise TransferNetworkError('Received more data than declared')
                    f.write(data); h.update(data); expected_index+=1
                elif msg.get('type') == TRANSFER_COMPLETE: break
                else: raise TransferNetworkError('Unexpected transfer message')
        digest=h.hexdigest()
        if received != meta.size or digest != meta.sha256: temp.unlink(missing_ok=True); await send_json(writer,{"type":TRANSFER_ACK,"ok":False}); raise TransferNetworkError('File integrity check failed')
        temp.replace(final)
        await send_json(writer,{"type":TRANSFER_ACK,"ok":True,"sha256":digest})
        return final
