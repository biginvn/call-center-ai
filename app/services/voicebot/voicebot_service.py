import os
import sys
import time
import json
import asyncio
import websockets
import wave
import pyaudio
from pydub import AudioSegment
from pydub.playback import play
import threading
import base64
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# SIP Configuration
SIP_DOMAIN = os.getenv('SIP_DOMAIN')
SIP_USER = os.getenv('SIP_USER')
SIP_PASS = os.getenv('SIP_PASS')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AGENT_ID = os.getenv('AGENT_ID')

# Additional OpenAI settings
OPENAI_MODE = os.getenv('OPENAI_MODE', 'realtime').lower()
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-realtime')
OPENAI_VOICE = os.getenv('OPENAI_VOICE', 'alloy')

try:
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
except ValueError:
    OPENAI_TEMPERATURE = 0.3

SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', 'You are a helpful voice assistant.')

SAMPLE_RATE = 16000
CHANNELS = 1

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Audio callback class for PJSIP
class AudioCallback(pj.AudioMedia):
    def __init__(self, call):
        pj.AudioMedia.__init__(self)
        self.call = call
        self.audio_queue = asyncio.Queue()
        self.is_active = True
        
    def onFrameRequested(self, frame):
        if not self.is_active:
            return
        if frame.type == pj.PJMEDIA_FRAME_TYPE_AUDIO:
            self.audio_queue.put_nowait(frame.buf)
            
    def stop(self):
        self.is_active = False

# Call class for handling SIP calls
class Call(pj.Call):
    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc
        self.audio_callback = None
        self.ws = None
        self.openai_thread = None
        self.call_id = call_id
        
    def onCallState(self, prm):
        ci = self.getInfo()
        print(f"Call state: {ci.stateText}")
        
        if ci.state == pj.PJSIP_INV_STATE_CONFIRMED:
            print("Call established, starting OpenAI Voice Agent")

            self.audio_callback = AudioCallback(self)
            call_slot = self.getAudioMedia(-1)
            call_slot.startTransmit(self.audio_callback)

            print("Using OpenAI Realtime API")
            self.openai_thread = threading.Thread(target=asyncio.run,
                                                 args=(self.start_openai_agent_realtime(),))
            self.openai_thread.start()
            
        elif ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            print("Call disconnected")
            if self.audio_callback:
                self.audio_callback.stop()
            if self.ws and not self.ws.closed:
                asyncio.run(self.ws.close())
            
    async def start_openai_agent_realtime(self):
        ws_url = (
            f"wss://api.openai.com/v1/realtime?"
            f"model={OPENAI_MODEL}&voice={OPENAI_VOICE}&temperature={OPENAI_TEMPERATURE}"
        )
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
        async with websockets.connect(ws_url, extra_headers=headers) as self.ws:
            session_update = {
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "model": OPENAI_MODEL,
                    "output_modalities": ["audio"],
                    "audio": {
                        "input": {
                            "format": {"type": "audio/pcm16", "sample_rate": SAMPLE_RATE},
                            "turn_detection": {"type": "server_vad"}
                        },
                        "output": {
                            "format": {"type": "audio/pcm16", "sample_rate": SAMPLE_RATE}
                        }
                    },
                    "instructions": SYSTEM_PROMPT
                }
            }
            await self.ws.send(json.dumps(session_update))
            await asyncio.gather(
                self.send_audio_to_openai_realtime(),
                self.receive_audio_from_openai_realtime()
            )
    
    async def send_audio_to_openai_realtime(self):
        while self.audio_callback and self.audio_callback.is_active:
            try:
                audio_chunk = await self.audio_callback.audio_queue.get()
                if audio_chunk and self.ws and not self.ws.closed:
                    audio_b64 = base64.b64encode(audio_chunk).decode('utf-8')
                    message = {
                        "type": "input_audio_buffer.append",
                        "audio": audio_b64
                    }
                    await self.ws.send(json.dumps(message))
            except Exception as e:
                error_msg = f"Error sending audio to OpenAI (Realtime): {e}"
                print(error_msg)
                break
    
    async def receive_audio_from_openai_realtime(self):
        try:
            while self.ws and not self.ws.closed:
                raw_msg = await self.ws.recv()
                if not raw_msg:
                    continue
                try:
                    message = json.loads(raw_msg)
                except Exception:
                    continue
                msg_type = message.get('type')
                if msg_type == 'response.output_audio.delta' and 'delta' in message:
                    try:
                        audio_bytes = base64.b64decode(message['delta'])
                        self.playback_audio(audio_bytes)
                    except Exception as decode_err:
                        print(f"Error decoding audio delta: {decode_err}")
        except Exception as e:
            error_msg = f"Error receiving audio from OpenAI (Realtime): {e}"
            print(error_msg)
    
    def playback_audio(self, audio_data):
        try:
            with wave.open("temp.wav", "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data)
            sound = AudioSegment.from_wav("temp.wav")
            play(sound)
            os.remove("temp.wav")
        except Exception as e:
            print(f"Error playing back audio: {e}")

# Account class for SIP registration
class Account(pj.Account):
    def __init__(self, ep):
        pj.Account.__init__(self)
        self.ep = ep
        
    def onRegState(self, prm):
        ai = self.getInfo()
        print(f"Registration state: {ai.regStatusText} ({ai.regStatus})")
        
    def onIncomingCall(self, prm):
        print("Incoming call...")
        call = Call(self, prm.callId)
        call_prm = pj.CallOpParam()
        call_prm.statusCode = 200
        call.answer(call_prm)

# Main function
def main():
    if not all([SIP_DOMAIN, SIP_USER, SIP_PASS, OPENAI_API_KEY, AGENT_ID]):
        error_msg = "Error: Missing environment variables. Please check your .env file."
        print(error_msg)
        sys.exit(1)
        
    ep_cfg = pj.EpConfig()
    ep = pj.Endpoint()
    ep.libCreate()
    ep.libInit(ep_cfg)
    
    transport_cfg = pj.TransportConfig()
    transport_cfg.port = 5060
    transport = ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)
    
    ep.libStart()
    
    acc_cfg = pj.AccountConfig()
    acc_cfg.idUri = f"sip:{SIP_USER}@{SIP_DOMAIN}"
    acc_cfg.regConfig.registrarUri = f"sip:{SIP_DOMAIN}"
    cred = pj.AuthCredInfo("digest", "*", SIP_USER, 0, SIP_PASS)
    acc_cfg.sipConfig.authCreds.append(cred)
    
    acc = Account(ep)
    acc.create(acc_cfg)
    
    print(f"SIP client registered as {SIP_USER}@{SIP_DOMAIN}")
    print("Waiting for incoming calls...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ep.libDestroy()
        ep.libDelete()

if __name__ == "__main__":
    main()
