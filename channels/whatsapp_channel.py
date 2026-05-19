"""WhatsApp channel for OCTO gateway (via Twilio or Meta Cloud API)."""
from __future__ import annotations
import json
import logging
import threading
from typing import Any

from .base import BaseChannel

logger = logging.getLogger(__name__)


class WhatsAppChannel(BaseChannel):
    """
    WhatsApp channel using Meta's Cloud API webhook.

    Config keys:
        token           – WhatsApp Cloud API bearer token
        phone_number_id – Your phone number ID from Meta Business Manager
        verify_token    – Webhook verification token
        port            – Local webhook port (default: 8765)
    """

    def __init__(self, config: dict):
        super().__init__("whatsapp", config)
        self._token      = config.get("token", "")
        self._phone_id   = config.get("phone_number_id", "")
        self._verify     = config.get("verify_token", "octo_verify")
        self._port       = int(config.get("port", 8765))

    def start(self) -> None:
        if not self._token or not self._phone_id:
            logger.warning("[WhatsApp] Not configured — channel disabled")
            return
        self._running = True
        self._thread  = threading.Thread(target=self._webhook_server, daemon=True, name="octo-whatsapp")
        self._thread.start()
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
                    body   = json.loads(self.rfile.read(length) or b"{}")
                    self.send_response(200)
                    self.end_headers()
                    try:
                        for entry in body.get("entry", []):
                            for change in entry.get("changes", []):
                                msgs = change.get("value", {}).get("messages", [])
                                for msg in msgs:
                                    if msg.get("type") == "text":
                                        user_id = msg.get("from", "")
                                        text    = msg.get("text", {}).get("body", "").strip()
                                        if user_id and text:
                                            channel._emit(user_id, text)
                    except Exception as e:
                        logger.error("[WhatsApp] Parse error: %s", e)

                def log_message(self, *args):
                    pass  # silence access logs

            server = HTTPServer(("0.0.0.0", self._port), Handler)
            while self._running:
                server.handle_request()
        except Exception as e:
            logger.error("[WhatsApp] Webhook server error: %s", e)

    def send(self, user_id: str, text: str) -> None:
        try:
            import requests
            url  = f"https://graph.facebook.com/v18.0/{self._phone_id}/messages"
            data = {"messaging_product": "whatsapp", "to": user_id,
                    "type": "text", "text": {"body": text[:4096]}}
            requests.post(url, json=data,
                         headers={"Authorization": f"Bearer {self._token}"}, timeout=30)
        except Exception as e:
            logger.error("[WhatsApp] Send failed: %s", e)
