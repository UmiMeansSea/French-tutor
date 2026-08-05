import os
import time
import ctypes
import wave
import re

VOICE_AVAILABLE = False
TTS_AVAILABLE = False
EDGE_TTS_AVAILABLE = False

# Graceful import fallbacks
try:
    try:
        import pyaudio
    except ImportError:
        import pyaudiowpatch as pyaudio
        import sys
        sys.modules['pyaudio'] = pyaudio

    import sounddevice as sd
    import speech_recognition as sr
    from faster_whisper import WhisperModel
    VOICE_AVAILABLE = True
    
    # Load the ML model once globally for "antigravity" speed
    # Using int8 quantization keeps it light on the CPU
    whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
except Exception as e:
    VOICE_AVAILABLE = False

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    pass

try:
    import edge_tts
    import asyncio
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

async def _synthesize_edge_tts(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def speak_french(text, speed=1000, mentor_style="clara"):
    if not text or not str(text).strip():
        return
    
    # Isolate TTS Audio: Strip all markdown symbols (*, _, `, #, [], etc.) before feeding to edge-tts
    clean_text = re.sub(r'[\*\_`#\[\]]', '', str(text)).strip()
    if not clean_text:
        return
    
    temp_file = os.path.abspath("temp_response.mp3")
    s_clean = str(mentor_style).lower()
    voice = "fr-FR-HenriNeural" if "derek" in s_clean or "coach" in s_clean else "fr-FR-DeniseNeural"

    try:
        if EDGE_TTS_AVAILABLE:
            asyncio.run(_synthesize_edge_tts(clean_text, voice, temp_file))
        elif TTS_AVAILABLE:
            tts = gTTS(text=clean_text, lang='fr')
            tts.save(temp_file)
        else:
            return
        
        winmm = ctypes.windll.winmm
        winmm.mciSendStringW(f'open "{temp_file}" type mpegvideo alias mymp3', None, 0, 0)
        winmm.mciSendStringW('play mymp3 wait', None, 0, 0)
        winmm.mciSendStringW('close mymp3', None, 0, 0)
        
        time.sleep(0.1)  # Release file handle lock
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
    except Exception:
        # Suppress TTS errors to ensure conversation loop continues
        try:
            ctypes.windll.winmm.mciSendStringW('close mymp3', None, 0, 0)
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass


def listen_to_mic(silence_threshold=4.0, sample_rate=16000, max_duration=30.0, prompt_first=True):
    if not VOICE_AVAILABLE:
        print("\n[Microphone Error: Voice input packages (faster-whisper/SpeechRecognition) are missing.]")
        return ""

    # Allow typing override
    if prompt_first:
        try:
            user_prompt_input = input("\nPress [Enter] when ready to speak (or type message, [Ctrl+C] to cancel): ").strip()
            if user_prompt_input:
                return user_prompt_input
        except KeyboardInterrupt:
            print("\n[Turn Canceled 🛑. Resetting prompt...]\n")
            return ""

    temp_wav = os.path.abspath("temp_input.wav")
    print("\n[Listening... 🎤 Speak clearly in French or English. Timeout: 15s | Pause limit: 20s]")
    
    recognizer = sr.Recognizer()
    recognizer.operation_timeout = 15.0
    recognizer.pause_threshold = silence_threshold

    try:
        with sr.Microphone(sample_rate=sample_rate) as source:
            # Replaces the complex numpy RMS arrays by delegating to the recognizer's ambient noise calibration
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=max_duration)
            print("[Silence detected. Processing Speech... ⚡]")
            
            with open(temp_wav, "wb") as f:
                f.write(audio.get_wav_data())
                
            # Transcribe seamlessly (Language auto-detection enabled)
            segments, info = whisper_model.transcribe(temp_wav, beam_size=5)
            transcription = " ".join([segment.text for segment in segments]).strip()
            
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass
                
            if not transcription:
                print("\n[Notice: Audio captured, but speech could not be recognized. Please speak slightly louder or closer to the mic.]")
                return ""
            
            # Command Interception
            # Whisper generates punctuation natively, so we strip it to ensure commands trigger correctly
            cmd_keywords = ["speed", "call", "dossier", "stats", "profile", "roleplay", "shadow", "story", "milestones", "badges", "hangout", "quit", "exit"]
            transcription_lower = transcription.lower()
            
            if transcription_lower.startswith("/") or any(kw in transcription_lower for kw in cmd_keywords):
                return re.sub(r'[^\w\s/]', '', transcription).strip()
                
            return transcription

    except sr.WaitTimeoutError:
        print("\n[Listening timed out.]")
        return ""
    except Exception as e:
        print(f"\n[Microphone Error: {e}]")
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
        return ""