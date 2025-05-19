



import json

from app.websocket.ari.Config.ari_config import AUTH_HDR, WS_URL
from app.websocket.ari.Models.ari_models import AriEventType
from app.websocket.ari.events import *
import websocket as ws_client
def on_message(ws, message):
    ev = json.loads(message)
    et = ev.get("type")
    print(f"EVENT: {et}")
    if et == AriEventType.STASIS_START:
        handle_stasis_start(ev)
    elif et == AriEventType.CHANNEL_STATE_CHANGE:
        handle_channel_state_change(ev)
    elif et == AriEventType.CHANNEL_HANGUP_REQUEST:
        handle_hangup_request(ev)
    elif et == AriEventType.CHANNEL_ENTERED_BRIDGE:
        handle_channel_enter_bridge(ev)
    elif et == AriEventType.RECORDING_FINISHED:
        handle_recording_finished(ev)
    elif et == AriEventType.BRIDGE_DESTROYED:
        handle_bridge_destroy(ev)


def on_open(ws):
    print("Connected to Asterisk")

def on_close(ws):
    print("Disconnected from Asterisk")

def on_error(ws, error):
    print(f"Error: {error}")

def run_ws_monitor():
    ws = ws_client.WebSocketApp(
        WS_URL,
        header = [f"Authorization: {AUTH_HDR}"],
        on_message=on_message,
        on_open=on_open,
        on_close=on_close,
        on_error=on_error
    )
    ws.run_forever()


