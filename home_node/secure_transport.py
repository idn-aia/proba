"""Authenticated transport helpers.

The v1 server authenticates peers with Ed25519 before transferring files.
This module provides a small optional TLS wrapper for deployments that also
want confidentiality on the LAN. Plain asyncio streams remain the default.
"""
from __future__ import annotations
import ssl

def make_server_context(certfile, keyfile, cafile=None, require_client_cert=False):
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(certfile,keyfile)
    if cafile:
        ctx.load_verify_locations(cafile)
        ctx.verify_mode=ssl.CERT_REQUIRED if require_client_cert else ssl.CERT_OPTIONAL
    return ctx

def make_client_context(cafile=None, certfile=None, keyfile=None, check_hostname=False):
    ctx=ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cafile)
    ctx.check_hostname=check_hostname
    if cafile is None: ctx.verify_mode=ssl.CERT_NONE
    if certfile and keyfile: ctx.load_cert_chain(certfile,keyfile)
    return ctx
