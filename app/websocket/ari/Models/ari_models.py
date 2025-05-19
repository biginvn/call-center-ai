from pydantic import BaseModel
from typing import List, Optional, TypedDict, Set
from datetime import datetime
from enum import Enum


class CallerInfo(BaseModel):
    name: str
    number: str

class ConnectedInfo(BaseModel):
    name: str
    number: str

class DialplanInfo(BaseModel):
    context: str
    exten: str
    priority: int
    app_name: str
    app_data: str

class ChannelInfo(BaseModel):
    id: str
    name: str
    state: str
    protocol_id: str
    caller: CallerInfo
    connected: ConnectedInfo
    accountcode: Optional[str]
    dialplan: DialplanInfo
    creationtime: datetime
    language: str

class StasisStartEvent(BaseModel):
    type: str
    timestamp: datetime
    args: List[str]
    channel: ChannelInfo
    asterisk_id: str
    application: str



class CallSession(BaseModel):
    call_id: str
    caller_chan: str
    agent_chan: Optional[str]
    bridge_id: Optional[str]
    conversation_id: Optional[str]
    up: Set[str]
    bridged: Set[str]
    status: str  # e.g. "incoming", "ringing", "connected", "finished"
    snoops: Optional[list[str]]  # nếu có monitoring
    recording_name: Optional[str]
    recording_finished: Optional[bool]
    agent_ext: Optional[str]


class AriEventType(str, Enum):
    STASIS_START = "StasisStart"
    CHANNEL_STATE_CHANGE = "ChannelStateChange"
    CHANNEL_HANGUP_REQUEST = "ChannelHangupRequest"
    CHANNEL_ENTERED_BRIDGE = "ChannelEnteredBridge"
    RECORDING_FINISHED = "RecordingFinished"
    BRIDGE_DESTROYED = "BridgeDestroyed"
