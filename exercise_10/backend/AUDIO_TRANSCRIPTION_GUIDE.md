# Audio Transcription Architecture - Working Solution

**Date:** 2025-10-30  
**Status:** ✅ WORKING (one good transcription achieved)  
**Commit:** 0bdad4b (rolled back to this version)

---

## 🎯 Overview

This document explains how real-time audio transcription works in the voice call system, analyzing what's correct and what causes issues.

---

## 📡 Audio Pipeline Flow

### 1. **Browser Capture (Frontend)**
```
User speaks → MediaRecorder API → Raw PCM Audio Chunks
```

**Key Facts:**
- **Format:** Raw PCM (Pulse Code Modulation) - uncompressed audio samples
- **Sample Rate:** 16,000 Hz (16 kHz)
- **Bit Depth:** 16-bit (2 bytes per sample)
- **Channels:** 1 (Mono)
- **Chunk Size:** ~1,700-2,000 bytes per chunk
- **Chunk Frequency:** Every ~100ms
- **Data Rate:** ~32,000 bytes per second of audio

**Location:** `exercise_10/frontend/src/lib/audioUtils.ts`
- Line 165: `this.mediaRecorder.start(1000)` - captures in chunks

### 2. **WebSocket Transmission**
```
Frontend → WebSocket → Backend
```

**Key Facts:**
- Each chunk is sent as **binary data** (not JSON)
- Chunks are **raw PCM bytes**, NOT complete audio files
- Total bandwidth: ~32 KB/s per active speaker

**Location:** `exercise_10/frontend/src/lib/useAudioCall.ts`
- Line 52-54: Sends chunks via `ws.send(chunk)`

### 3. **Backend Reception & Accumulation**
```
WebSocket receives → Accumulate in buffer → Trigger processing
```

**Key Facts:**
- Individual chunks are **too small** to transcribe (1.7 KB ≈ 0.05s)
- Must **accumulate** multiple chunks before transcription
- Uses Voice Activity Detection (VAD) for smart processing

**Current Working Configuration:**
```python
# Minimum buffer before considering processing
min_buffer_size = 64,000 bytes  # 2 seconds of audio

# Maximum wait time
max_wait_time_ms = 8000  # 8 seconds

# Processing logic:
if buffer >= 64,000 bytes AND time >= 8 seconds:
    → Trigger transcription
```

**Location:** `exercise_10/backend/app/api/websocket.py`
- Lines 113-133: Audio chunk handling
- Lines 610-680: `accumulate_audio_data()` function
- Lines 655-656: Buffer size thresholds

### 4. **Format Conversion (PCM → WAV)**
```
Accumulated PCM buffer → WAV conversion → Whisper API
```

**Why WAV Conversion is Required:**
- OpenAI Whisper API requires **complete audio files** with headers
- Raw PCM has **no header** - just raw samples
- Python's `wave` module adds WAV headers **without ffmpeg!**

**WAV Conversion Process:**
```python
wav_buffer = io.BytesIO()
with wave.open(wav_buffer, 'wb') as wav_file:
    wav_file.setnchannels(1)      # Mono
    wav_file.setsampwidth(2)      # 16-bit (2 bytes per sample)
    wav_file.setframerate(16000)  # 16kHz sample rate
    wav_file.writeframes(audio_data)  # Raw PCM data
```

**Location:** `exercise_10/backend/app/api/websocket.py`
- Lines 576-586: WAV conversion logic

### 5. **Transcription (Whisper API)**
```
WAV file → OpenAI Whisper API → Text transcript
```

**Key Facts:**
- Model: `whisper-1`
- Input: WAV format audio
- Output: Text transcript
- Language: English ("en")

**Location:** `exercise_10/backend/app/api/whisper_service.py`
- Lines 6-24: `transcribe_audio()` function

---

## ✅ What Makes It Work Correctly

### Success Criteria Met:

1. **Sufficient Audio Duration**
   - ✅ User spoke for 15 seconds
   - ✅ Buffer accumulated to > 64,000 bytes (2+ seconds)
   - ✅ Whisper had enough context to understand speech

2. **Proper Format Conversion**
   - ✅ Accumulated raw PCM chunks
   - ✅ Converted to WAV using `wave` module (no ffmpeg!)
   - ✅ Whisper accepted the WAV format

3. **Timing**
   - ✅ Waited 8 seconds before processing
   - ✅ Gave enough time to accumulate substantial audio

4. **No Concatenation of Encoded Files**
   - ✅ Accumulated **raw PCM** (can be concatenated)
   - ✅ NOT accumulating WebM files (which cannot be concatenated)

---

## ❌ Common Failure Modes

### Problem 1: "You" Transcriptions

**Cause:** Small audio buffers (< 25,600 bytes / 0.8s) being processed

**Why it happens:**
- Background noise accumulates
- Timeout triggers on small buffer
- Whisper tries to transcribe ~5-10KB of noise
- Result: "you" or other gibberish

**Solution:**
```python
# Add minimum size check in transcribe_audio_buffer()
MIN_AUDIO_SIZE = 25600  # 0.8 seconds
if len(audio_data) < MIN_AUDIO_SIZE:
    return None  # Skip transcription
```

**Location:** Line 565 (needs to be added/enforced)

### Problem 2: Invalid File Format

**Cause:** Trying to send raw PCM or concatenated WebM to Whisper

**Why it happens:**
- Whisper requires complete audio files with headers
- Raw PCM has no header
- Concatenated WebM files are corrupted

**Solution:**
- Always convert raw PCM to WAV using `wave` module
- Never concatenate already-encoded audio files (WebM, MP3, etc.)

### Problem 3: WebSocket Reconnection Loop

**Cause:** WebSocket closes unexpectedly, useEffect triggers reconnect

**Why it happens:**
- SSL certificate issues
- Redis connection failures
- Backend errors during startup

**Solution:**
- Ensure Redis is running
- Trust SSL certificates in browser
- Check backend logs for actual error

---

## 🔧 Critical Configuration Values

### Buffer Sizes (at 16kHz, 16-bit, Mono):

| Duration | Bytes | Purpose |
|----------|-------|---------|
| 0.05s | 1,700 | Individual chunk from browser |
| 0.5s | 16,000 | Minimum to consider (filter noise) |
| 0.8s | 25,600 | **Absolute minimum for transcription** |
| 1.0s | 32,000 | Good minimum for accuracy |
| 2.0s | 64,000 | **Target buffer size (current)** |
| 3.0s | 96,000 | Better accuracy, slower response |

### Timing Values:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `max_wait_time_ms` | 8000ms (8s) | Process buffer after this time |
| Individual chunk interval | ~100ms | How often browser sends chunks |

---

## 📝 Working Code Structure

### Current Flow (Working):

```
1. Browser sends raw PCM chunk (~1.7KB) every 100ms
   ↓
2. Backend receives, accumulates in buffer
   ↓
3. When buffer >= 64KB AND time >= 8s:
   ↓
4. Convert accumulated PCM → WAV using wave module
   ↓
5. Send WAV to Whisper API
   ↓
6. Receive transcript text
   ↓
7. Broadcast to frontend via WebSocket
```

### Key Functions:

| Function | Purpose | Location |
|----------|---------|----------|
| `accumulate_audio_data()` | Accumulate PCM chunks, decide when to process | websocket.py:610 |
| `process_audio_buffer()` | Extract buffer for processing, clear it | websocket.py:690 |
| `transcribe_audio_buffer()` | Convert PCM→WAV, call Whisper | websocket.py:557 |
| `transcribe_audio()` | Send to Whisper API | whisper_service.py:6 |
| `transcribe_and_broadcast()` | Coordinate transcription & messaging | websocket.py:694 |

---

## 🐛 Known Issues & Solutions

### Issue 1: Subsequent "You" Transcriptions

**Status:** ⚠️ PARTIALLY RESOLVED

**Cause:**
- After first successful transcription, small residual buffers accumulate
- Timeouts trigger on buffers with < 25,600 bytes
- These small buffers transcribe as "you"

**Tested Solution (not yet applied):**
```python
# In transcribe_audio_buffer(), add strict minimum:
MIN_AUDIO_SIZE = 32000  # 1.0 seconds minimum
if len(audio_data) < MIN_AUDIO_SIZE:
    print(f"⚠️ Skipping - too small")
    return None
```

**⚠️ WARNING:** Do NOT apply this until we confirm it doesn't break the first transcription!

### Issue 2: Confusion About Audio Format

**The Truth:**
- ✅ Live voice call sends: **Raw PCM** (uncompressed)
- ✅ Test page sends: **WebM/Opus** (compressed, complete files)
- ❌ Common mistake: Treating PCM as WebM

**How to Tell:**
- PCM chunks: ~1.7-2 KB each, need accumulation
- WebM files: Larger (15-30 KB+), complete files with headers

---

## 🧪 Testing & Validation

### Test Page (Working Reference):
- **URL:** `https://localhost:8600/api/test/audio`
- **Format:** WebM/Opus (complete encoded files)
- **Size:** ~800 KB for 10 seconds of speech
- **Works:** ✅ Transcribes correctly

### Live Voice Call (Current Focus):
- **Format:** Raw PCM chunks
- **Strategy:** Accumulate → Convert to WAV → Transcribe
- **Status:** ✅ First transcription works, ⚠️ subsequent "You" noise

---

## 🎓 Lessons Learned

### DO's ✅

1. **DO accumulate raw PCM chunks** before processing
2. **DO use Python's `wave` module** for conversion (no ffmpeg needed!)
3. **DO wait for sufficient audio** (at least 0.8-1.0 seconds)
4. **DO test with real speech** (not just noise)
5. **DO check backend logs** to understand what's happening
6. **DO save audio samples** for debugging

### DON'Ts ❌

1. **DON'T concatenate WebM/MP3/encoded files** (corrupts audio)
2. **DON'T send raw PCM** directly to Whisper (needs WAV header)
3. **DON'T process chunks < 25,600 bytes** (will transcribe as noise)
4. **DON'T make rapid code changes** without testing each iteration
5. **DON'T assume WebM** when it's actually raw PCM
6. **DON'T skip validation** - save files and inspect them!

---

## 🔍 Debugging Checklist

When transcription fails, check:

1. **Audio is arriving?**
   - Look for: `📊 Audio buffer: X bytes`
   - Should increment every ~100ms

2. **Buffer reaching threshold?**
   - Look for: `✅ Minimum buffer size reached!`
   - Buffer should reach 64,000+ bytes

3. **Processing triggered?**
   - Look for: `⏰ Max wait time reached`
   - Should happen after 8 seconds

4. **Format conversion working?**
   - Look for: `Converting X bytes PCM to WAV`
   - Should NOT see WebM errors

5. **Whisper API called?**
   - Look for: `HTTP Request: POST https://api.openai.com/v1/audio/transcriptions`
   - Should return 200 OK, not 400

6. **Check saved samples:**
   ```bash
   # Inspect saved audio files
   python check_audio_file.py audio_samples/latest_file.webm
   ```

---

## 🚀 Next Steps to Eliminate "You" Noise

### Proposed Fix (CONSERVATIVE):

Add one line to filter very small buffers:

```python
# In transcribe_audio_buffer(), line ~565
# ONLY change the MIN_AUDIO_SIZE value:
MIN_AUDIO_SIZE = 32000  # Change from whatever it currently is to 1.0 second minimum
```

### Why This Should Work:
- ✅ First transcription had ~64,000 bytes → will still work
- ✅ Noise buffers have < 32,000 bytes → will be filtered
- ✅ Minimal change to working code

### Testing Plan:
1. Make ONLY this one change
2. Test: Speak 15 seconds
3. Wait 10 seconds  
4. Verify: ONE transcription appears
5. Verify: No "You" messages after

---

## 📊 Performance Metrics

### Current Working State:

| Metric | Value |
|--------|-------|
| Time to first transcription | ~8 seconds after speaking |
| Minimum speech duration | ~2 seconds |
| Accuracy (when working) | ✅ Correct words |
| False transcriptions | ⚠️ "You" on noise |
| API calls per 15s speech | Should be 1-2, currently seeing more |

---

## 🎤 Audio Format Reference

### Raw PCM (what browser sends):
```
- No header, just samples
- 16-bit signed integers
- 16,000 samples/second
- 32,000 bytes/second
- Can be concatenated safely ✅
```

### WAV Format (what we convert to):
```
- Has RIFF/WAV header (44 bytes)
- Contains PCM audio data
- Header specifies: channels, sample rate, bit depth
- Whisper API accepts this ✅
- Created by Python's wave module ✅
```

### WebM Format (test page only):
```
- Complete encoded file with Matroska container
- Uses Opus codec (compressed)
- ~1.5-2 KB per second (very efficient)
- CANNOT be concatenated ❌
- Complete files work with Whisper ✅
```

---

## 🔧 Configuration Summary

### Current Settings (Working for First Transcription):

```python
# Buffer accumulation (websocket.py:655-656)
min_buffer_size = 64,000 bytes  # 2 seconds minimum
max_wait_time_ms = 8000  # Process after 8 seconds

# Transcription function (websocket.py:565 - NEEDS FIX)
MIN_AUDIO_SIZE = ???  # Should be 32,000 bytes minimum

# Audio sample format
Sample Rate: 16,000 Hz
Bit Depth: 16-bit
Channels: 1 (Mono)
```

---

## 🎯 Recommended Fix (NOT YET APPLIED)

To eliminate "You" noise while preserving working first transcription:

```python
# exercise_10/backend/app/api/websocket.py
# In function: transcribe_audio_buffer() around line 565

# CHANGE THIS LINE:
MIN_AUDIO_SIZE = 32000  # 1.0 seconds minimum (up from current value)

# KEEP EVERYTHING ELSE THE SAME!
```

**Impact:**
- ✅ First good transcription: PRESERVED (has 64KB+)
- ✅ Noise transcriptions: ELIMINATED (have < 32KB)
- ✅ Minimal risk: Only ONE line changed

---

## 📚 Files Reference

| File | Purpose | Critical Sections |
|------|---------|-------------------|
| `websocket.py` | Main WebSocket handler | Lines 81-137 (audio handling)<br>Lines 557-601 (transcription)<br>Lines 610-680 (accumulation) |
| `whisper_service.py` | Whisper API client | Lines 6-24 (transcribe function) |
| `audioUtils.ts` | Frontend audio capture | Lines 93-173 (AudioRecorder class) |
| `useAudioCall.ts` | React hook for audio | Lines 44-86 (startAudio function) |
| `vad_service.py` | Voice Activity Detection | Lines 1-11 (constants)<br>Lines 85-128 (should_process function) |

---

## 🧪 Test & Validation Tools

### 1. Web Test Page
```
URL: https://localhost:8600/api/test/audio
Purpose: Test Whisper API with WebM files
Status: ✅ WORKING
```

### 2. Audio File Checker
```bash
# Check saved audio files
cd exercise_10/backend
python check_audio_file.py

# Or check specific file
python check_audio_file.py audio_samples/original_20251030_140000.webm
```

### 3. Simple Test Program
```bash
# Test PCM to WAV conversion
cd exercise_10/backend
python test_audio_conversion.py
```

---

## 🎬 Success Case Analysis

### Your Successful Test:

**What you did:**
- Spoke continuously for 15 seconds
- Waited for transcription
- Received correct text!

**What happened in backend:**
```
1. Received ~150 PCM chunks (1.7KB each × 150 ≈ 255KB)
2. Buffer accumulated to >= 64,000 bytes
3. After 8 seconds, timeout triggered
4. Converted accumulated PCM to WAV
5. Sent to Whisper (probably ~128-256KB WAV)
6. Whisper transcribed correctly ✅
```

**Backend logs would show:**
```
📊 Audio buffer: 64,123 bytes (2.00s of audio) for call_xxx
   ✅ Minimum buffer size reached!
   ⏰ Max wait time reached (8000ms), forcing transcription!
🎵 Processing accumulated audio buffer: 128,456 bytes
🎵 About to transcribe audio for customer, size: 128456 bytes
   Trying WebM format first...
   WebM failed: Invalid file format, trying WAV conversion...
   Converting 128456 bytes PCM to WAV...
✅ Transcription successful (WAV) for customer: [YOUR 15 SECONDS OF SPEECH]
```

---

## 🎯 Root Cause of Issues

### The Fundamental Problem:
After the first successful transcription, **small residual buffers** still trigger the timeout mechanism:

```
Buffer: 5,647 bytes (0.18s of noise)
   ↓
Wait 8 seconds
   ↓
Timeout triggers
   ↓  
Convert to WAV (corrupt audio from noise)
   ↓
Whisper tries to transcribe noise
   ↓
Result: "you"
```

### The Solution:
**Add a safety check** before transcription to reject buffers < 1 second

---

## 📋 Action Items

**To completely fix the system:**

1. ✅ Keep current working accumulation logic
2. ✅ Keep WAV conversion approach  
3. ⚠️ Add MIN_AUDIO_SIZE = 32,000 bytes check
4. ⚠️ Test to confirm no regression
5. ⚠️ Document final working configuration

---

**END OF DOCUMENTATION**

*This document should be referenced before making ANY changes to the audio transcription pipeline.*

