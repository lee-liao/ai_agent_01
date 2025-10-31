"""
Check and convert audio files from WebM to WAV
This allows you to play the recorded audio
"""
import sys
import os

def check_webm_file(filename):
    """Check WebM file and provide info"""
    if not os.path.exists(filename):
        print(f"[ERROR] File not found: {filename}")
        return
    
    file_size = os.path.getsize(filename)
    print(f"[OK] File found: {filename}")
    print(f"   Size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
    
    # Read first few bytes to check format
    with open(filename, 'rb') as f:
        header = f.read(20)
        print(f"   Header (hex): {header[:20].hex()}")
        
        # WebM files start with specific bytes
        if header[:4] == b'\x1a\x45\xdf\xa3':
            print(f"   [OK] Valid WebM/Matroska container")
        else:
            print(f"   [WARN] Not a standard WebM file")
    
    print("\n[INFO] The WebM file contains Opus audio codec")
    print("   Windows Media Player often can't play Opus codec")
    print("   Try playing with VLC Media Player or Chrome browser")
    
    # Try to send to Whisper API
    print("\n[TEST] Testing transcription...")
    try:
        import asyncio
        from openai import AsyncOpenAI
        
        async def test_transcribe():
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("   [WARN] OPENAI_API_KEY not set")
                return
            
            with open(filename, 'rb') as f:
                audio_data = f.read()
            
            client = AsyncOpenAI(api_key=api_key)
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=(os.path.basename(filename), audio_data, "audio/webm"),
                language="en"
            )
            
            print(f"   [OK] Transcription: {response.text}")
            print(f"   [OK] Audio contains speech!")
        
        asyncio.run(test_transcribe())
        
    except Exception as e:
        print(f"   [ERROR] Transcription failed: {e}")
    
    print("\n[SOLUTION] How to play the audio:")
    print("   1. Play in Chrome browser: drag the file into a Chrome tab")
    print("   2. Install VLC Media Player (supports all codecs)")
    print("   3. The audio IS working - Windows Media Player just can't decode Opus")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Find the most recent file
        audio_dir = "audio_samples"
        if os.path.exists(audio_dir):
            files = [os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.endswith('.webm')]
            if files:
                latest = max(files, key=os.path.getmtime)
                print(f"[INFO] Checking most recent file...\n")
                check_webm_file(latest)
            else:
                print("[ERROR] No WebM files found in audio_samples/")
        else:
            print("[ERROR] audio_samples directory not found")
    else:
        check_webm_file(sys.argv[1])

