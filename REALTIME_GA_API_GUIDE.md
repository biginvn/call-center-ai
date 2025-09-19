# OpenAI Realtime API - GA (Generally Available) Implementation

This document explains the implementation of the OpenAI Realtime API GA interface in your call center AI application. The GA version introduces ephemeral client secrets that can be safely used in client-side applications.

## 🚀 What's New in GA

### Key Changes from Beta to GA:
- **Single Endpoint**: Only one endpoint `POST /v1/realtime/client_secrets` (replaces multiple beta endpoints)
- **Ephemeral Tokens**: Client secrets that expire automatically and are safe for client-side use
- **Direct Client Connection**: Clients can connect directly to OpenAI without server proxying
- **New Voices**: Added Cedar and Marin voices for enhanced quality
- **Updated Model**: Uses the new `gpt-realtime` model
- **Removed Beta Header**: No longer requires `OpenAI-Beta: realtime=v1` header
- **New WebRTC URL**: Updated SDP endpoint to `/v1/realtime/calls`
- **Session Type Required**: Must specify session type (`realtime` or `transcription`)
- **Updated Event Structure**: Changed event names and configuration locations

## 📋 Implementation Overview

### Files Modified:
1. `app/dto/openai_dto.py` - Added Realtime API DTOs
2. `app/services/openai_service.py` - Added client secret creation method
3. `app/api/openai_api.py` - Added REST endpoint for client secrets
4. `test_realtime_ga_api.py` - Comprehensive test suite

### New DTOs:
- `RealtimeAudioOutput` - Audio output configuration
- `RealtimeAudio` - Audio settings container
- `RealtimeSessionConfig` - Session configuration
- `RealtimeSessionRequest` - Request payload
- `RealtimeSessionResponse` - Response with client secret

## 🔧 API Endpoint

### POST `/api/openai/realtime/client_secrets`

Generates ephemeral client secrets for OpenAI Realtime API sessions.

#### Request Format:
```json
{
  "session": {
    "type": "realtime",
    "model": "gpt-realtime",
    "audio": {
      "output": {"voice": "marin"}
    },
    "instructions": "Optional instructions for the AI",
    "temperature": 0.7,
    "max_response_output_tokens": 4096
  }
}
```

#### Response Format:
```json
{
  "value": "ek_68af296e8e408191a1120ab6383263c2",
  "expires_at": 1234567890,
  "session_id": "optional_session_id"
}
```

## 🎙️ Voice Options

### Standard Voices:
- `alloy` - Neutral, balanced
- `echo` - Clear, professional  
- `fable` - Warm, storytelling
- `onyx` - Deep, authoritative
- `nova` - Bright, energetic
- `shimmer` - Gentle, soothing

### Advanced Voices (Enhanced Quality):
- `sage` - Wise, contemplative
- `coral` - Friendly, approachable
- `verse` - Poetic, expressive
- `ballad` - Musical, melodic
- `ash` - Calm, steady
- `cedar` - **NEW** - Rich, natural voice
- `marin` - **NEW** - Clear, professional voice (recommended default)

## 🔌 Client-Side Usage

### 1. Get Client Secret from Your Backend

```javascript
const sessionConfig = {
    session: {
        type: "realtime",
        model: "gpt-realtime",
        audio: {
            output: { voice: "marin" }
        }
    }
};

const response = await fetch("/api/openai/realtime/client_secrets", {
    method: "POST",
    headers: {
        "Authorization": `Bearer ${userJwtToken}`,
        "Content-Type": "application/json"
    },
    body: JSON.stringify(sessionConfig)
});

const data = await response.json();
const clientSecret = data.value; // e.g. ek_68af296e8e408191a1120ab6383263c2
```

### 2. Connect Directly to OpenAI

```javascript
// GA WebSocket connection (no beta header required)
const websocket = new WebSocket(
    "wss://api.openai.com/v1/realtime?model=gpt-realtime",
    [],
    {
        headers: {
            "Authorization": `Bearer ${clientSecret}`
            // ✅ No OpenAI-Beta header needed for GA
        }
    }
);

websocket.onopen = () => {
    console.log("Connected to OpenAI Realtime API");
    
    // Send session configuration with required structure
    websocket.send(JSON.stringify({
        type: "session.update",
        session: {
            type: "realtime",              // Required: session type
            model: "gpt-realtime",         // Required: model specification
            instructions: "You are a helpful assistant",
            audio: {
                output: { voice: "marin" } // Nested audio configuration
            }
        }
    }));
};

websocket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    // Handle new GA event names
    switch (message.type) {
        case "response.output_text.delta":           // ✅ New event name
            handleTextDelta(message.delta);
            break;
        case "response.output_audio.delta":          // ✅ New event name
            handleAudioDelta(message.delta);
            break;
        case "response.output_audio_transcript.delta": // ✅ New event name
            handleTranscriptDelta(message.delta);
            break;
        default:
            console.log("Received:", message);
    }
};

websocket.onerror = (error) => {
    console.error("WebSocket error:", error);
};
```

### 3. WebRTC Implementation (GA)

For WebRTC connections, use the new SDP endpoint:

```javascript
// WebRTC setup with GA endpoint
const pc = new RTCPeerConnection();

// Create offer
const offer = await pc.createOffer();
await pc.setLocalDescription(offer);

// Get remote SDP from GA endpoint
const baseUrl = "https://api.openai.com/v1/realtime/calls"; // ✅ New GA URL
const sdpResponse = await fetch(baseUrl, {
    method: "POST",
    body: offer.sdp,
    headers: {
        Authorization: `Bearer ${clientSecret}`,    // Use ephemeral token
        "Content-Type": "application/sdp",
        // ✅ No beta header needed
    },
});

const sdp = await sdpResponse.text();
const answer = { type: "answer", sdp };
await pc.setRemoteDescription(answer);
```
```

## 🔒 Security Benefits

### Ephemeral Tokens:
- ✅ Safe for client-side use (browsers, mobile apps)
- ✅ Automatically expire
- ✅ Limited scope (only for realtime sessions)
- ✅ No API key exposure

### Authentication Flow:
1. Client authenticates with your backend
2. Backend generates ephemeral token via OpenAI
3. Client uses token to connect directly to OpenAI
4. Token expires automatically (no cleanup needed)

## 📱 Use Cases

### Perfect For:
- **Voice Assistants**: Real-time conversation interfaces
- **Call Centers**: AI-powered customer support
- **Live Translation**: Real-time language translation
- **Interactive Demos**: Product demonstrations with voice
- **Mobile Apps**: Voice-enabled mobile applications
- **Web Applications**: Browser-based voice interactions

### Architecture Benefits:
- **Reduced Latency**: Direct client-to-OpenAI connection
- **Scalability**: Less server load (no audio proxying)
- **Cost Effective**: Reduced bandwidth usage on your servers
- **Better Performance**: Native WebRTC/WebSocket optimization

## 🧪 Testing

### Run the Test Suite:
```bash
python test_realtime_ga_api.py
```

### Manual API Testing:
```bash
curl -X POST "http://localhost:8000/api/openai/realtime/client_secrets" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session": {
      "type": "realtime",
      "model": "gpt-realtime",
      "audio": {
        "output": {"voice": "marin"}
      }
    }
  }'
```

### Expected Response:
```json
{
  "value": "ek_68af296e8e408191a1120ab6383263c2",
  "expires_at": 1234567890
}
```

## ⚙️ Configuration Options

### GA Session Configuration Structure:
```json
{
  "session": {
    "type": "realtime",                   // Required: "realtime" or "transcription"
    "model": "gpt-realtime",             // Required: the model to use
    "audio": {                           // Optional: nested audio configuration
      "output": {
        "voice": "marin"                 // Voice selection (nested structure)
      },
      "input_audio_format": "pcm16",     // Optional: input format
      "output_audio_format": "pcm16"     // Optional: output format
    },
    "instructions": "System prompt",      // Optional: AI instructions
    "turn_detection": {                   // Optional: voice activity detection
      "type": "server_vad",
      "threshold": 0.5,
      "prefix_padding_ms": 300,
      "silence_duration_ms": 500
    },
    "temperature": 0.7,                   // Optional: response randomness
    "max_response_output_tokens": 4096    // Optional: max response length
  }
}
```

### Session Types:

#### 1. Realtime (Speech-to-Speech):
```json
{
  "session": {
    "type": "realtime",
    "model": "gpt-realtime",
    "audio": {
      "output": { "voice": "marin" }
    },
    "instructions": "You are a helpful call center assistant"
  }
}
```

#### 2. Transcription (Speech-to-Text):
```json
{
  "session": {
    "type": "transcription",
    "model": "gpt-realtime",
    "instructions": "Transcribe the following audio accurately"
  }
}
```

### WebSocket Event Structure (GA):

#### Session Update Event:
```javascript
websocket.send(JSON.stringify({
    type: "session.update",
    session: {                          // ✅ Nested under session
        type: "realtime",              // ✅ Required session type
        model: "gpt-realtime",         // ✅ Model specification
        audio: {                       // ✅ Nested audio config
            output: { voice: "marin" }
        },
        instructions: "Be helpful and professional"
    }
}));
```
```

## ❌ Error Handling

### Common Errors:
- **401 Unauthorized**: Invalid or missing JWT token
- **403 Forbidden**: User not authenticated
- **429 Rate Limited**: OpenAI API rate limit exceeded
- **500 Internal Error**: OpenAI API issues or configuration problems

### Error Response Format:
```json
{
  "detail": "Error description",
  "status_code": 500
}
```

## 🚀 Production Deployment

### Environment Variables:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Dependencies:
```bash
pip install openai>=1.3.0 aiohttp>=3.9.0 fastapi pydantic
```

### Performance Considerations:
- Client secrets are ephemeral (handle expiration gracefully)
- Monitor OpenAI API usage and rate limits
- Implement proper error handling for network issues
- Consider connection pooling for high-traffic scenarios

## 📈 Monitoring

### Key Metrics to Track:
- Client secret generation rate
- Token expiration handling
- WebSocket connection success rate
- Audio quality and latency
- Error rates and types

### Logging:
The implementation includes comprehensive logging for:
- Client secret creation success/failure
- API request/response details
- Error conditions and troubleshooting info

## 🔄 Migration from Beta to GA

### Critical Breaking Changes

#### 1. **Beta Header Removal**
**Before (Beta):**
```javascript
// Beta required this header for all requests
headers: {
    "Authorization": `Bearer ${apiKey}`,
    "OpenAI-Beta": "realtime=v1",  // ❌ Remove this for GA
    "Content-Type": "application/json"
}
```

**After (GA):**
```javascript
// GA does not use the beta header
headers: {
    "Authorization": `Bearer ${clientSecret}`, // Use ephemeral token
    "Content-Type": "application/json"
}
```

#### 2. **Ephemeral API Keys**
**Before (Beta):** Multiple endpoints for different session types
```javascript
// Beta had separate endpoints
POST /v1/realtime/sessions
POST /v1/transcription/sessions
```

**After (GA):** Single unified endpoint
```javascript
// GA uses one endpoint for all session types
POST /v1/realtime/client_secrets
```

#### 3. **WebRTC SDP URL Change**
**Before (Beta):**
```javascript
const baseUrl = "https://api.openai.com/v1/realtime/sessions"; // ❌ Old URL
```

**After (GA):**
```javascript
const baseUrl = "https://api.openai.com/v1/realtime/calls"; // ✅ New URL
const model = "gpt-realtime";
const sdpResponse = await fetch(baseUrl, {
    method: "POST",
    body: offer.sdp,
    headers: {
        Authorization: `Bearer YOUR_EPHEMERAL_KEY_HERE`,
        "Content-Type": "application/sdp",
    },
});

const sdp = await sdpResponse.text();
const answer = { type: "answer", sdp };
await pc.setRemoteDescription(answer);
```

#### 4. **Session Type Required**
**Before (Beta):** Session type was implicit
```javascript
// Beta - session type was inferred
{
    "instructions": "Be helpful",
    "voice": "alloy"
}
```

**After (GA):** Must explicitly specify session type
```javascript
// GA - session type is required
{
    "type": "session.update",
    "session": {
        "type": "realtime",        // ✅ Required: "realtime" or "transcription"
        "instructions": "Be helpful",
        "audio": {
            "output": { "voice": "alloy" }
        }
    }
}
```

#### 5. **Configuration Structure Changes**
**Before (Beta):**
```javascript
// Beta - flat configuration structure
ws.send(JSON.stringify({
    type: "session.update",
    instructions: "Be extra nice today!",
    voice: "alloy"
}));
```

**After (GA):**
```javascript
// GA - nested session configuration
ws.send(JSON.stringify({
    type: "session.update",
    session: {
        type: "realtime",
        model: "gpt-realtime",
        instructions: "Be extra nice today!",
        audio: {
            output: { voice: "marin" }
        }
    }
}));
```

#### 6. **Event Name Changes**
**Before (Beta):**
```javascript
// Beta event names
response.text.delta                    // ❌ Old
response.audio.delta                   // ❌ Old  
response.audio_transcript.delta        // ❌ Old
```

**After (GA):**
```javascript
// GA event names
response.output_text.delta             // ✅ New
response.output_audio.delta            // ✅ New
response.output_audio_transcript.delta // ✅ New
```

### Complete Migration Example

#### Beta Implementation:
```javascript
// Beta WebSocket connection
const ws = new WebSocket("wss://api.openai.com/v1/realtime", {
    headers: {
        "Authorization": `Bearer ${apiKey}`,
        "OpenAI-Beta": "realtime=v1"  // ❌ Beta header
    }
});

ws.on("open", function() {
    // Beta session configuration
    ws.send(JSON.stringify({
        type: "session.update",
        instructions: "Be helpful",
        voice: "alloy",
        input_audio_format: "pcm16"
    }));
});

ws.on("message", function(data) {
    const event = JSON.parse(data);
    if (event.type === "response.text.delta") {  // ❌ Old event name
        console.log(event.delta);
    }
});
```

#### GA Implementation:
```javascript
// Step 1: Get ephemeral client secret from your backend
const sessionConfig = {
    session: {
        type: "realtime",
        model: "gpt-realtime",
        audio: {
            output: { voice: "marin" }
        }
    }
};

const response = await fetch("/api/openai/realtime/client_secrets", {
    method: "POST",
    headers: {
        "Authorization": `Bearer ${userJwtToken}`,
        "Content-Type": "application/json"
    },
    body: JSON.stringify(sessionConfig)
});

const { value: clientSecret } = await response.json();

// Step 2: Connect using ephemeral token (no beta header)
const ws = new WebSocket("wss://api.openai.com/v1/realtime?model=gpt-realtime", {
    headers: {
        "Authorization": `Bearer ${clientSecret}`  // ✅ Ephemeral token
        // ✅ No beta header needed
    }
});

ws.on("open", function() {
    // GA session configuration with nested structure
    ws.send(JSON.stringify({
        type: "session.update",
        session: {                          // ✅ Nested under session
            type: "realtime",              // ✅ Required session type
            model: "gpt-realtime",         // ✅ Model specification
            instructions: "Be helpful",
            audio: {                       // ✅ Nested audio config
                output: { voice: "marin" },
                input_audio_format: "pcm16"
            }
        }
    }));
});

ws.on("message", function(data) {
    const event = JSON.parse(data);
    if (event.type === "response.output_text.delta") {  // ✅ New event name
        console.log(event.delta);
    }
});
```

### Migration Checklist

#### ✅ **Required Changes:**
- [ ] Remove `OpenAI-Beta: realtime=v1` header from all requests
- [ ] Update ephemeral key generation to use `/v1/realtime/client_secrets`
- [ ] Update WebRTC SDP URL to `/v1/realtime/calls`
- [ ] Add required `type: "realtime"` to session configurations
- [ ] Nest audio configuration under `audio.output.voice`
- [ ] Update event handlers for new event names:
  - `response.text.delta` → `response.output_text.delta`
  - `response.audio.delta` → `response.output_audio.delta`
  - `response.audio_transcript.delta` → `response.output_audio_transcript.delta`
- [ ] Update session configuration structure to use nested `session` object
- [ ] Specify model explicitly (`gpt-realtime`)

#### 🔧 **Optional Improvements:**
- [ ] Use new voices (Cedar, Marin) for better quality
- [ ] Implement proper ephemeral token expiration handling
- [ ] Add error handling for GA-specific error responses
- [ ] Update client-side code to handle new event structures

### Session Types

#### Realtime (Speech-to-Speech):
```javascript
{
    "session": {
        "type": "realtime",           // For conversational AI
        "model": "gpt-realtime",
        "audio": {
            "output": { "voice": "marin" }
        }
    }
}
```

#### Transcription:
```javascript
{
    "session": {
        "type": "transcription",      // For speech-to-text only
        "model": "gpt-realtime"
    }
}
```

---

This implementation provides a secure, scalable, and performant way to integrate OpenAI's Realtime API into your call center application using the latest GA interface.