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

VAD_AVAILABLE = False
try:
    import webrtcvad
    vad_detector = webrtcvad.Vad(3)  # Aggressiveness Level 3
    VAD_AVAILABLE = True
except (ImportError, Exception):
    try:
        from silero_vad import load_silero_vad, get_speech_timestamps
        silero_model = load_silero_vad()
        VAD_AVAILABLE = True
        webrtcvad = None
    except Exception:
        VAD_AVAILABLE = False
        webrtcvad = None

async def _synthesize_edge_tts(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

import threading

def _play_tts_async(clean_text, voice, temp_file):
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
        try:
            ctypes.windll.winmm.mciSendStringW('close mymp3', None, 0, 0)
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass

def play_thinking_filler(mentor_style="clara"):
    """
    Phase 2 Local Rate Limit TTS Fallback: Plays a lightweight local filler phrase
    (e.g., 'Hmm, laisse-moi réfléchir...') to mask network delay when API backoff occurs.
    """
    filler_text = "Hmm, laisse-moi réfléchir un instant..."
    speak_french(filler_text, mentor_style=mentor_style)

def speak_french(text, speed=1000, mentor_style="clara"):
    if not text or not str(text).strip():
        return
    
    clean_text = re.sub(r'[\*\_`#\[\]]', '', str(text)).strip()
    if not clean_text:
        return
    
    temp_file = os.path.abspath(f"temp_resp_{int(time.time() * 1000)}.mp3")
    s_clean = str(mentor_style).lower()
    voice = "fr-FR-HenriNeural" if "derek" in s_clean or "coach" in s_clean else "fr-FR-DeniseNeural"

    # Launch background thread so UI/input loop is not blocked during audio playback
    t = threading.Thread(target=_play_tts_async, args=(clean_text, voice, temp_file), daemon=True)
    t.start()


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
            
            raw_pcm = audio.get_raw_data(convert_rate=16000, convert_width=2)
            
            # Phase 1 Compute Frugality: Voice Activity Detection Frame Filtering
            if VAD_AVAILABLE:
                has_speech = False
                if webrtcvad is not None:
                    # webrtcvad requires 10, 20, or 30ms frames (at 16kHz 16-bit mono = 320, 640, 960 bytes)
                    frame_size = 960
                    speech_frames = 0
                    for i in range(0, len(raw_pcm) - frame_size, frame_size):
                        frame = raw_pcm[i:i + frame_size]
                        if len(frame) == frame_size and vad_detector.is_speech(frame, 16000):
                            speech_frames += 1
                            if speech_frames >= 2:
                                has_speech = True
                                break
                else:
                    # Silero VAD fallback
                    import torch
                    audio_tensor = torch.from_numpy(np.frombuffer(raw_pcm, dtype=np.int16).astype(np.float32) / 32768.0)
                    timestamps = get_speech_timestamps(audio_tensor, silero_model, sampling_rate=16000)
                    has_speech = len(timestamps) > 0
                
                if not has_speech:
                    print("\n[VAD Frugality 🔇: Silent/background noise frame dropped. Skipping Whisper CPU inference.]")
                    return ""

            print("[Speech detected via VAD. Processing Transcription... ⚡]")
            
            with open(temp_wav, "wb") as f:
                f.write(audio.get_wav_data())
                
            # Transcribe seamlessly with Franglish initial_prompt bias to prevent decoder hallucination on code-switching
            franglish_prompt = "Bonjour, hello! Je parle français and English mixed together. Comment ça va, thank you!"
            segments, info = whisper_model.transcribe(temp_wav, beam_size=3, initial_prompt=franglish_prompt)
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