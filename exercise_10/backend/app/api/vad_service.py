import numpy as np
import struct
from typing import List, Tuple
import asyncio

# VAD (Voice Activity Detection) Constants
VAD_SILENCE_THRESHOLD = 0.005  # Energy threshold for silence detection (0-1.0)
VAD_SPEECH_THRESHOLD = 0.02    # Energy threshold for speech detection (0-1.0)
VAD_SILENCE_DURATION_MS = 500  # Minimum silence duration to trigger chunking (ms)
VAD_MIN_CHUNK_DURATION_MS = 1000  # Minimum chunk duration before considering for transcription (ms)
VAD_BUFFER_SIZE_SAMPLES = 100     # Size of energy level buffer for smoothing

class VADError(Exception):
    """Custom exception for VAD-related errors"""
    pass

def calculate_audio_energy(audio_data: bytes) -> float:
    """
    Calculate the energy level of audio data for VAD.
    Returns a normalized energy value between 0.0 and 1.0
    
    Args:
        audio_data: Raw audio bytes (assumed to be 16-bit PCM)
        
    Returns:
        Normalized energy level (0.0 to 1.0)
    """
    if not audio_data or len(audio_data) < 4:
        return 0.0
    
    try:
        # Convert bytes to numpy array (assuming 16-bit PCM)
        # For WebM/Opus, we'll need to handle differently, but for VAD approximation this works
        samples = struct.unpack(f'{len(audio_data)//2}h', audio_data[:len(audio_data)//2*2])
        if not samples:
            return 0.0
            
        # Calculate RMS energy
        energy = np.sqrt(np.mean(np.array(samples, dtype=np.float64) ** 2))
        
        # Normalize to 0-1 range (16-bit audio has max value of 32767)
        normalized_energy = energy / 32767.0
        return min(1.0, max(0.0, normalized_energy))
    except Exception as e:
        print(f"⚠️ Error calculating audio energy: {e}")
        return 0.0

def is_speech_detected(energy_level: float) -> bool:
    """
    Check if the energy level indicates speech activity
    
    Args:
        energy_level: Normalized energy level (0.0 to 1.0)
        
    Returns:
        True if speech is detected, False otherwise
    """
    return energy_level >= VAD_SPEECH_THRESHOLD

def is_silence_detected(energy_levels: List[float], duration_ms: int = VAD_SILENCE_DURATION_MS) -> bool:
    """
    Check if silence has been detected for the specified duration.
    Looks at recent energy levels to determine if there's been sustained low energy (silence).
    
    Args:
        energy_levels: List of recent energy levels
        duration_ms: Minimum silence duration to trigger detection
        
    Returns:
        True if sustained silence detected, False otherwise
    """
    if not energy_levels:
        return False
    
    # Calculate how many samples we need to check for the silence duration
    # Assuming roughly 20ms per audio chunk (typical for WebRTC)
    samples_needed = max(1, duration_ms // 20)
    
    # Get the most recent samples
    recent_samples = energy_levels[-samples_needed:]
    
    # Check if all recent samples are below the silence threshold
    return all(energy < VAD_SILENCE_THRESHOLD for energy in recent_samples)

def should_process_audio_chunk(
    call_id: str,
    current_time: float,
    energy_levels: List[float],
    last_processing_time: float,
    chunk_duration_ms: int = VAD_MIN_CHUNK_DURATION_MS
) -> bool:
    """
    Determine if we should process the accumulated audio buffer.
    Returns True if we should process (based on time or VAD).
    
    Args:
        call_id: Call identifier
        current_time: Current timestamp
        energy_levels: List of recent energy levels
        last_processing_time: Timestamp of last processing
        chunk_duration_ms: Minimum chunk duration before processing
        
    Returns:
        True if audio should be processed, False otherwise
    """
    # Check if enough time has passed since last processing
    time_elapsed = (current_time - last_processing_time) * 1000  # Convert to milliseconds
    
    # Process if we've exceeded the minimum chunk duration
    if time_elapsed >= chunk_duration_ms:
        # Check if we have energy levels recorded
        if energy_levels:
            # Check for sustained silence to trigger processing
            # But also allow processing based on time alone for responsiveness
            if is_silence_detected(energy_levels):
                print(f"⏸️ [VAD-{call_id}] Silence detected, processing audio chunk")
                return True
            else:
                # If no silence detected but enough time has passed, still process
                # This ensures we don't miss transcriptions in continuous speech
                print(f"⏰ [VAD-{call_id}] Time threshold reached ({time_elapsed:.0f}ms >= {chunk_duration_ms}ms), processing audio chunk")
                return True
        else:
            # No energy levels recorded but enough time passed, process anyway
            print(f"⏰ [VAD-{call_id}] Time threshold reached with no energy data, processing audio chunk")
            return True
    
    return False

async def accumulate_audio_chunk(
    call_id: str,
    audio_chunk: bytes,
    audio_buffer: bytearray,
    energy_buffer: List[float]
) -> bool:
    """
    Accumulate audio chunk in buffer and determine if we should process it.
    Returns True if the chunk should be processed for transcription.
    
    Args:
        call_id: Call identifier
        audio_chunk: Incoming audio data
        audio_buffer: Buffer to accumulate audio data
        energy_buffer: Buffer to accumulate energy levels
        
    Returns:
        True if the chunk should be processed for transcription
    """
    current_time = asyncio.get_event_loop().time()
    
    # Calculate energy level for VAD
    energy_level = calculate_audio_energy(audio_chunk)
    
    # Store energy level for silence detection
    energy_buffer.append(energy_level)
    # Keep only recent energy levels to avoid memory issues
    if len(energy_buffer) > VAD_BUFFER_SIZE_SAMPLES:
        energy_buffer = energy_buffer[-VAD_BUFFER_SIZE_SAMPLES:]
    
    # Add chunk to buffer
    audio_buffer.extend(audio_chunk)
    print(f"📊 [VAD-{call_id}] Accumulated audio chunk: {len(audio_chunk)} bytes (total: {len(audio_buffer)} bytes)")
    
    # Check if we should process the accumulated buffer
    return should_process_audio_chunk(call_id, current_time, energy_buffer, 0.0)

async def process_audio_buffer(
    call_id: str,
    audio_buffer: bytearray,
    energy_buffer: List[float]
) -> bytes:
    """
    Process the accumulated audio buffer and return the audio data for transcription.
    Clears the buffer after processing.
    
    Args:
        call_id: Call identifier
        audio_buffer: Buffer containing accumulated audio data
        energy_buffer: Buffer containing accumulated energy levels
        
    Returns:
        Audio data for transcription
    """
    # Get the accumulated audio data
    audio_data = bytes(audio_buffer)
    
    # Clear the buffers
    audio_buffer.clear()
    energy_buffer.clear()
    
    print(f"🎵 [VAD-{call_id}] Processing accumulated audio buffer: {len(audio_data)} bytes")
    return audio_data

# Export constants for use in other modules
__all__ = [
    'VADError',
    'VAD_SILENCE_THRESHOLD',
    'VAD_SPEECH_THRESHOLD',
    'VAD_SILENCE_DURATION_MS',
    'VAD_MIN_CHUNK_DURATION_MS',
    'calculate_audio_energy',
    'is_speech_detected',
    'is_silence_detected',
    'should_process_audio_chunk',
    'accumulate_audio_chunk',
    'process_audio_buffer'
]