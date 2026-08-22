from __future__ import annotations
from dataclasses import asdict
from node_auth import *
from framing import send_json, receive_json
from protocol import AUTH_CHALLENGE, AUTH_RESPONSE, AUTH_RESULT, encode_bytes, decode_bytes

class NodeAuthNetworkError(Exception): pass

def _get_public_key_bytes(identity) -> bytes:
    value=identity.public_key_bytes
    if callable(value): value=value()
    if not isinstance(value, bytes): raise TypeError("identity.public_key_bytes must return bytes")
    return value

class NodeAuthNetworkClient:
    def __init__(self, identity, expected_remote_node_id): self.identity=identity; self.expected_remote_node_id=expected_remote_node_id
    async def authenticate(self, reader, writer):
        challenge_msg=await receive_json(reader)
        if challenge_msg.get("type") != AUTH_CHALLENGE: raise NodeAuthNetworkError("Expected authentication challenge")
        challenge=AuthChallenge(decode_bytes(challenge_msg["challenge"]),challenge_msg["sender_node_id"],challenge_msg["receiver_node_id"])
        if challenge.receiver_node_id not in ("*", self.identity.node_id): raise NodeAuthNetworkError("Challenge addressed to another node")
        response=create_auth_response(self.identity,challenge,self.expected_remote_node_id)
        await send_json(writer,{"type":AUTH_RESPONSE,"node_id":response.node_id,"public_key":encode_bytes(response.public_key),"signature":encode_bytes(response.signature)})
        result=await receive_json(reader)
        if result.get("type") != AUTH_RESULT or not result.get("ok"): raise NodeAuthNetworkError("Authentication failed")
        return response

class NodeAuthNetworkServer:
    def __init__(self, identity, expected_remote_node_id=None): self.identity=identity; self.expected_remote_node_id=expected_remote_node_id
    async def authenticate(self, reader, writer):
        challenge=create_auth_challenge(self.identity.node_id, self.expected_remote_node_id or "*")
        await send_json(writer,{"type":AUTH_CHALLENGE,"challenge":encode_bytes(challenge.challenge),"sender_node_id":self.identity.node_id,"receiver_node_id":challenge.receiver_node_id})
        msg=await receive_json(reader)
        if msg.get("type") != AUTH_RESPONSE: raise NodeAuthNetworkError("Expected authentication response")
        response=AuthResponse(msg["node_id"],decode_bytes(msg["public_key"]),decode_bytes(msg["signature"]))
        expected=self.expected_remote_node_id or response.node_id
        valid=verify_auth_response(response,challenge,expected,self.identity.node_id)
        await send_json(writer,{"type":AUTH_RESULT,"ok":valid,"node_id":self.identity.node_id})
        if not valid: raise NodeAuthNetworkError("Authentication failed")
        return response
