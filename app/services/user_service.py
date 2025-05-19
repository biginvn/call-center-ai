from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


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