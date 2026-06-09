"""Thin synchronous OSC client for talking to AbletonOSC.

AbletonOSC listens on UDP 11000 and replies on 11001, echoing the request
address. We send a message then block for the matching reply.
"""

import os
import threading
from typing import Iterable, Tuple, Any

from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

REMOTE_HOST = os.environ.get("ABLETON_OSC_HOST", "127.0.0.1")
REMOTE_PORT = int(os.environ.get("ABLETON_OSC_PORT", "11000"))
LOCAL_PORT = int(os.environ.get("ABLETON_OSC_REPLY_PORT", "11001"))

# An Ableton tick is 100ms; allow headroom for processing.
# Large clips (hundreds of notes) need a longer window for the reply.
DEFAULT_TIMEOUT = 5.0


class AbletonOSCClient:
    def __init__(
        self,
        hostname: str = REMOTE_HOST,
        port: int = REMOTE_PORT,
        client_port: int = LOCAL_PORT,
    ):
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self._handle_osc)
        self.server = ThreadingOSCUDPServer(("0.0.0.0", client_port), dispatcher)
        self.server_thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.server_thread.start()
        self._handlers = {}
        self.client = SimpleUDPClient(hostname, port)

    def _handle_osc(self, address: str, *params):
        fn = self._handlers.get(address)
        if fn:
            fn(address, params)

    def send(self, address: str, params: Iterable = ()):
        self.client.send_message(address, list(params))

    def query(
        self, address: str, params: tuple = (), timeout: float = DEFAULT_TIMEOUT
    ) -> Tuple[Any, ...]:
        rv = None
        event = threading.Event()

        def received(_addr, p):
            nonlocal rv
            rv = p
            event.set()

        self._handlers[address] = received
        self.send(address, params)
        got = event.wait(timeout)
        self._handlers.pop(address, None)
        if not got:
            raise RuntimeError(
                "No response from AbletonOSC for %s "
                "(is Live running with AbletonOSC selected as a Control Surface?)"
                % address
            )
        return rv

    def stop(self):
        self.server.shutdown()
        self.server_thread.join(timeout=1)
