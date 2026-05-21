from __future__ import annotations
import json
import logging
import asyncio
import threading
from typing import Any
import requests

from channels.base import Channel
from channels.message_bus import InboundMessage, InboundMessageType, MessageBus, OutboundMessage

logger = logging.getLogger(__name__)

class WhatsAppChannel(Channel):
    """
    WhatsApp channel using Meta's Cloud API webhook, fully integrated with
    OCTO's MessageBus.
    """

    def __init__(self, bus: MessageBus, config: dict[str, Any]) -> None:
        super().__init__(name="whatsapp", bus=bus, config=config)
        self._token = config.get("token", config.get("auth_token", ""))
        self._phone_id = config.get("phone_number_id", config.get("account_sid", ""))
        self._verify = config.get("verify_token", "octo_verify")
        self._port = int(config.get("port", 8765))
        self._running = False
        self._server = None
        self._thread = None

    async def start(self) -> None:
        if not self._token or not self._phone_id:
            logger.warning("[WhatsApp] Not configured — channel disabled")
            return
        self._running = True
        self._thread = threading.Thread(target=self._webhook_server, daemon=True, name="octo-whatsapp")
        self._thread.start()
        self._running = True
        logger.info("[WhatsApp] Webhook server on port %d", self._port)

    def _webhook_server(self) -> None:
        try:
            from http.server import BaseHTTPRequestHandler, HTTPServer
            import urllib.parse

            channel = self
            class Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
                    if params.get("hub.verify_token") == channel._verify:
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(params.get("hub.challenge", "").encode())
                    else:
                        self.send_response(403)
                        self.end_headers()

                def do_POST(self):
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length) or b"{}")
                    self.send_response(200)
                    self.end_headers()
                    try:
                        for entry in body.get("entry", []):
                            for change in entry.get("changes", []):
                                msgs = change.get("value", {}).get("messages", [])
                                for msg in msgs:
                                    if msg.get("type") == "text":
                                        user_id = msg.get("from", "")
                                        text = msg.get("text", {}).get("body", "").strip()
                                        if user_id and text:
                                            inbound = channel._make_inbound(
                                                chat_id=user_id,
                                                user_id=user_id,
                                                text=text,
                                                msg_type=InboundMessageType.CHAT
                                            )
                                            loop = getattr(channel.bus, "_loop", None) or asyncio.get_event_loop()
                                            if loop and loop.is_running():
                                                asyncio.run_coroutine_threadsafe(
                                                    channel.bus.publish_inbound(inbound),
                                                    loop
                                                )
                                            else:
                                                asyncio.run(channel.bus.publish_inbound(inbound))
                    except Exception as e:
                        logger.error("[WhatsApp] Parse error: %s", e)

                def log_message(self, *args):
                    pass

            self._server = HTTPServer(("0.0.0.0", self._port), Handler)
            while self._running:
                self._server.handle_request()
        except Exception as e:
            logger.error("[WhatsApp] Webhook server error: %s", e)

    async def stop(self) -> None:
        self._running = False
        if self._server:
            try:
                self._server.server_close()
            except Exception:
                pass
        logger.info("[WhatsApp] Webhook server stopped")

    async def send(self, msg: OutboundMessage) -> None:
        try:
            url = f"https://graph.facebook.com/v18.0/{self._phone_id}/messages"
            data = {
                "messaging_product": "whatsapp",
                "to": msg.chat_id,
                "type": "text",
                "text": {"body": msg.text[:4096]}
            }
            res = requests.post(
                url,
                json=data,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=30
            )
            res.raise_for_status()
        except Exception as e:
            logger.error("[WhatsApp] Send failed: %s", e)

    def pair_qr(self) -> None:
        logger.info("[WhatsApp] QR pairing requested")
