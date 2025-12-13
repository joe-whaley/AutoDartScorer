import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Optional, Callable, Any

import requests
import websocket


@dataclass
class AutodartsConfig:
    base_url: str   # e.g. "http://10.0.0.127:3180"
    api_key: str    # not needed for ws://10.0.0.127:3180/api/events, but kept for future
    board_id: str   # also for future/REST use
    timeout: float = 3.0


class AutodartsAPIClient:
    """Client for talking to the local Autodarts board manager."""

    def __init__(self, cfg: AutodartsConfig):
        self.cfg = cfg
        self.session = requests.Session()

        # Base REST URL (optional, for later)
        self.base_url = self.cfg.base_url.rstrip("/")

        # Derive WebSocket URL from base_url: http://... -> ws://.../api/events
        self.ws_url = self.base_url.replace("http", "ws") + "/api/events"

        # WebSocket state
        self.ws_app: Optional[websocket.WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self._running = False

        # Callback the scorer can register to receive parsed dart events
        # Signature: callback(event_dict: dict) -> None
        self.on_event: Optional[Callable[[dict], None]] = None

    # ---------- REST (optional, for later) ----------

    def _url(self, path: str) -> str:
        return self.base_url + "/" + path.lstrip("/")

    def get_state(self) -> dict:
        """Example REST call placeholder."""
        url = self._url("api/state")  # TODO: update if/when you want REST
        resp = self.session.get(url, timeout=self.cfg.timeout)
        resp.raise_for_status()
        return resp.json()

    # ---------- WebSocket logic ----------

    def _on_message(self, ws: websocket.WebSocketApp, message: str):
        """Internal handler for every WS message."""
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            print("[WS] Non-JSON message:", message)
            return

        if self.on_event is not None:
            try:
                self.on_event(data)
            except Exception as e:
                print("[WS] Error in on_event callback:", e)

    def _on_error(self, ws: websocket.WebSocketApp, error: Any):
        print("[WS] Error:", error)

    def _on_close(self, ws: websocket.WebSocketApp, close_status_code, close_msg):
        print(f"[WS] Closed: {close_status_code} {close_msg}")
        self._running = False

    def _on_open(self, ws: websocket.WebSocketApp):
        print("[WS] Connected to Autodarts events stream:", self.ws_url)

    def start_event_stream(self, daemon: bool = True):
        """Start the WebSocket connection in a background thread."""
        if self._running:
            print("[WS] Event stream already running")
            return

        self.ws_app = websocket.WebSocketApp(
            self.ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )

        def _run():
            self.ws_app.run_forever()

        self._running = True
        self.ws_thread = threading.Thread(target=_run, daemon=daemon)
        self.ws_thread.start()

    def stop_event_stream(self):
        """Gracefully stop the WebSocket stream."""
        self._running = False
        if self.ws_app is not None:
            try:
                self.ws_app.close()
            except Exception:
                pass
        if self.ws_thread is not None:
            self.ws_thread.join(timeout=2.0)


# ------------------------------
#  Standalone runner
# ------------------------------

def _segment_to_code(segment: dict) -> str:
    """Convert an Autodarts 'segment' dict into a DartConnect-style code."""
    name = segment.get("name")
    number = segment.get("number")
    bed = segment.get("bed", "").lower()

    if name == "25":
        return "25"
    if name == "Bull":
        return "Bull"

    if "triple" in bed:
        prefix = "T"
    elif "double" in bed:
        prefix = "D"
    elif "single" in bed:
        prefix = "S"
    else:
        prefix = "M"

    return f"{prefix}{number}"


def _print_dart(event: dict):
    """Callback to print dart segment and coordinates."""
    if event.get("type") != "state":
        return

    data = event.get("data", {})
    if data.get("event") != "Throw detected":
        return

    throws = data.get("throws", [])
    if not throws:
        return

    new_throw = throws[-1]
    segment = new_throw.get("segment", {})
    coords = new_throw.get("coords", {})

    code = _segment_to_code(segment)
    x = coords.get("x")
    y = coords.get("y")

    if x is not None and y is not None:
        print(f"{code} {x:.3f} {y:.3f}")
    else:
        print(f"{code} None None")


if __name__ == "__main__":
    """Run as a standalone dart event printer."""
    raw_base_url = os.getenv("AUTODARTS_BASE_URL", "http://10.0.0.127:3180")
    base_url = raw_base_url.strip().strip('"').strip("'")

    api_key = os.getenv("AUTODARTS_API_KEY", "REPLACE_ME")
    board_id = os.getenv("AUTODARTS_BOARD_ID", "REPLACE_ME")

    cfg = AutodartsConfig(base_url=base_url, api_key=api_key, board_id=board_id)
    autodarts = AutodartsAPIClient(cfg)
    autodarts.on_event = _print_dart
    autodarts.start_event_stream()

    print("AutoDartsClient standalone: streaming darts (segment x y). Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        autodarts.stop_event_stream()
        print("Stopped.")
