import os
import time
import ctypes
import wave

VOICE_AVAILABLE = False
TTS_AVAILABLE = False

# Graceful import fallbacks
try:
    import sounddevice as sd
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    pass

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
    import re
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

import numpy as np

def listen_to_mic(silence_threshold=4.0, sample_rate=16000, max_duration=30.0, prompt_first=True):
    if not VOICE_AVAILABLE:
        print("\n[Microphone Error: Voice input packages (sounddevice/SpeechRecognition) are missing.]")
        return ""

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
    recognizer.pause_threshold = 4.0  # 4-second pause window before cutting off

    # Primary SpeechRecognition Microphone path
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=20)
            text_fr = ""
            text_en = ""
            try:
                text_fr = recognizer.recognize_google(audio, language="fr-FR").strip()
            except Exception:
                pass
            try:
                text_en = recognizer.recognize_google(audio, language="en-US").strip()
            except Exception:
                pass
            
            cmd_keywords = ["speed", "call", "dossier", "stats", "profile", "roleplay", "shadow", "story", "milestones", "badges", "hangout", "quit", "exit"]
            if text_en.startswith("/") or any(kw in text_en.lower() for kw in cmd_keywords):
                return text_en
            if text_fr:
                return text_fr
            if text_en:
                return text_en
    except Exception:
        pass

    # Sounddevice fallback with extended thresholds
    audio_chunks = []
    silence_start = None
    start_time = time.time()
    recent_rms_levels = []
    SILENCE_RMS_THRESHOLD = 150

    def callback(indata, frames, time_info, status):
        nonlocal silence_start, SILENCE_RMS_THRESHOLD
        audio_chunks.append(indata.copy())
        rms = np.sqrt(np.mean(indata.astype(np.float32)**2))
        
        if len(recent_rms_levels) < 15:
            recent_rms_levels.append(rms)
            if len(recent_rms_levels) == 15:
                ambient_avg = np.mean(recent_rms_levels)
                SILENCE_RMS_THRESHOLD = max(100.0, ambient_avg * 1.6)
        
        if rms < SILENCE_RMS_THRESHOLD:
            if silence_start is None:
                silence_start = time.time()
        else:
            silence_start = None

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=callback, blocksize=int(sample_rate * 0.2)):
            while True:
                time.sleep(0.1)
                elapsed = time.time() - start_time
                if silence_start and (time.time() - silence_start >= silence_threshold) and len(audio_chunks) > 10:
                    print("[Silence detected. Processing Speech... ⚡]")
                    break
                if elapsed >= max_duration:
                    print("[Max duration reached. Processing Speech... ⚡]")
                    break

        if not audio_chunks:
            return ""

        recording = np.concatenate(audio_chunks, axis=0)

        max_val = np.max(np.abs(recording))
        if max_val > 50 and max_val < 18000:
            boost_factor = 22000.0 / float(max_val)
            recording = (recording.astype(np.float32) * boost_factor).clip(-32768, 32767).astype(np.int16)

        with wave.open(temp_wav, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(recording.tobytes())
            
        with sr.AudioFile(temp_wav) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.record(source)
            
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
            
        text_en = ""
        text_fr = ""
        
        try:
            text_fr = recognizer.recognize_google(audio, language="fr-FR").strip()
        except Exception:
            pass

        try:
            text_en = recognizer.recognize_google(audio, language="en-US").strip()
        except Exception:
            pass

        cmd_keywords = ["speed", "call", "dossier", "stats", "profile", "roleplay", "shadow", "story", "milestones", "badges", "hangout", "quit", "exit"]
        if text_en.startswith("/") or any(kw in text_en.lower() for kw in cmd_keywords):
            return text_en
        
        if text_fr:
            return text_fr
        if text_en:
            return text_en

        print("\n[Notice: Audio captured, but speech could not be recognized. Please speak slightly louder or closer to the mic.]")
        return ""
    except Exception as e:
        print(f"\n[Microphone Error: {e}]")
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
        return ""
