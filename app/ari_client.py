import ari
import asyncio
import websockets
import json
import logging
from typing import Dict, Optional
import wave
import numpy as np
from openai import AsyncOpenAI
import sounddevice as sd
import queue
import threading
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceBotARI:
    def __init__(self, host: str, port: int, username: str, password: str, app_name: str):
        self.client = ari.connect(f'http://{host}:{port}', username, password)
        self.app_name = app_name
        self.openai_client = AsyncOpenAI()
        self.audio_queue = queue.Queue()
        self.is_processing = False
        self.openai_ws = None
        
        # Đăng ký các event handlers
        self.client.on_channel_event('StasisStart', self.handle_stasis_start)
        self.client.on_channel_event('ChannelDtmfReceived', self.handle_dtmf)
        self.client.on_channel_event('PlaybackStarted', self.handle_playback_started)
        self.client.on_channel_event('PlaybackFinished', self.handle_playback_finished)

    async def connect_to_openai_realtime(self):
        """Kết nối tới OpenAI Realtime API"""
        try:
            url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            self.openai_ws = await websockets.connect(url, extra_headers=headers)
            logger.info("Connected to OpenAI Realtime API")
            
            # Start listening for messages
            asyncio.create_task(self.listen_openai_messages())
            
        except Exception as e:
            logger.error(f"Error connecting to OpenAI Realtime API: {str(e)}")
            raise

    async def listen_openai_messages(self):
        """Lắng nghe messages từ OpenAI Realtime API"""
        try:
            while True:
                message = await self.openai_ws.recv()
                data = json.loads(message)
                
                if data.get("type") == "transcription":
                    # Xử lý transcription
                    text = data.get("text", "")
                    logger.info(f"Received transcription: {text}")
                    
                    # Gửi text tới TTS để phát lại
                    await self.text_to_speech(text)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.error("OpenAI WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in listen_openai_messages: {str(e)}")

    async def handle_stasis_start(self, channel, event):
        """Xử lý khi cuộc gọi được chuyển vào Stasis"""
        try:
            caller_channel = channel
            logger.info(f"Received call from {caller_channel.json.get('caller', {}).get('number')}")
            
            # Kết nối tới OpenAI Realtime API
            await self.connect_to_openai_realtime()
            
            # Originate cuộc gọi tới voicebot
            voicebot_channel = await self.originate_voicebot()
            
            # Bridge hai cuộc gọi
            bridge = self.client.bridges.create(type='mixing')
            bridge.addChannel(channel=caller_channel.id)
            bridge.addChannel(channel=voicebot_channel.id)
            
            # Bắt đầu xử lý audio stream
            await self.start_audio_processing(caller_channel, voicebot_channel)
            
        except Exception as e:
            logger.error(f"Error in handle_stasis_start: {str(e)}")

    async def start_audio_processing(self, caller_channel, voicebot_channel):
        """Bắt đầu xử lý audio stream"""
        try:
            # Thiết lập WebSocket để nhận audio stream từ Asterisk
            ws_url = f"ws://{self.client.base_url}/ari/endpoints/PJSIP/voicebot/stream"
            async with websockets.connect(ws_url) as websocket:
                self.is_processing = True
                
                # Nhận audio stream từ WebSocket
                while self.is_processing:
                    try:
                        audio_data = await websocket.recv()
                        
                        # Gửi audio data tới OpenAI Realtime API
                        if self.openai_ws and self.openai_ws.open:
                            await self.openai_ws.send(json.dumps({
                                "type": "audio",
                                "data": audio_data
                            }))
                            
                    except websockets.exceptions.ConnectionClosed:
                        break
                    
        except Exception as e:
            logger.error(f"Error in audio processing: {str(e)}")
            self.is_processing = False

    async def text_to_speech(self, text):
        """Chuyển đổi text thành audio sử dụng OpenAI TTS API"""
        try:
            response = await self.openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            # Lưu audio response vào file tạm
            temp_file = "temp_response.mp3"
            with open(temp_file, "wb") as f:
                f.write(response.content)
            
            # Phát audio response
            if hasattr(self, 'voicebot_channel'):
                self.voicebot_channel.play(media=f"sound:{temp_file}")
                
        except Exception as e:
            logger.error(f"Error in text_to_speech: {str(e)}")

    async def originate_voicebot(self):
        """Originate cuộc gọi tới voicebot extension"""
        try:
            channel = self.client.channels.originate(
                endpoint='PJSIP/voicebot',
                app=self.app_name,
                appArgs='voicebot',
                callerId='VoiceBot <123>'
            )
            self.voicebot_channel = channel
            return channel
        except Exception as e:
            logger.error(f"Error originating call to voicebot: {str(e)}")
            raise

    def handle_dtmf(self, channel, event):
        """Xử lý DTMF events"""
        digit = event.get('digit')
        logger.info(f"Received DTMF: {digit}")

    def handle_playback_started(self, playback, event):
        """Xử lý khi bắt đầu phát audio"""
        logger.info("Playback started")

    def handle_playback_finished(self, playback, event):
        """Xử lý khi kết thúc phát audio"""
        logger.info("Playback finished")

    async def cleanup(self):
        """Dọn dẹp resources"""
        self.is_processing = False
        if self.openai_ws:
            await self.openai_ws.close()
        self.client.close()

    def run(self):
        """Chạy ARI client"""
        try:
            self.client.run(apps=self.app_name)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            asyncio.run(self.cleanup())

if __name__ == "__main__":
    # Cấu hình
    HOST = "localhost"
    PORT = 8088
    USERNAME = "admin"
    PASSWORD = "admin"
    APP_NAME = "nixxis"

    # Khởi tạo và chạy VoiceBot
    voicebot = VoiceBotARI(HOST, PORT, USERNAME, PASSWORD, APP_NAME)
    voicebot.run() 