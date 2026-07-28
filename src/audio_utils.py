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

def speak_french(text, speed=1000, mentor_style="clara"):
    if not TTS_AVAILABLE:
        return
    if not text.strip():
        return
    
    temp_file = os.path.abspath("temp_response.mp3")
    try:
        # Create TTS MP3 with natural native French speech
        tts = gTTS(text=text, lang='fr')
        tts.save(temp_file)
        
        # Play via Windows MCI (winmm.dll) at natural 100% speed without pitch distortion
        winmm = ctypes.windll.winmm
        
        # Open command
        open_command = f'open "{temp_file}" type mpegvideo alias mymp3'
        winmm.mciSendStringW(open_command, None, 0, 0)
        
        # Play command (blocks until finished)
        winmm.mciSendStringW('play mymp3 wait', None, 0, 0)
        
        # Close command
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

def listen_to_mic(silence_threshold=2.0, sample_rate=16000, max_duration=30.0):
    if not VOICE_AVAILABLE:
        print("\n[Microphone Error: Voice input packages (sounddevice/SpeechRecognition) are missing.]")
        return ""

    temp_wav = os.path.abspath("temp_input.wav")
    print("\n[Listening... 🎤 Speak clearly into your mic in French or English. Pause ~2s when finished]")
    
    audio_chunks = []
    silence_start = None
    start_time = time.time()
    
    # Adaptive noise floor tracking
    recent_rms_levels = []
    SILENCE_RMS_THRESHOLD = 150  # Sensitive default threshold

    def callback(indata, frames, time_info, status):
        nonlocal silence_start, SILENCE_RMS_THRESHOLD
        audio_chunks.append(indata.copy())
        rms = np.sqrt(np.mean(indata.astype(np.float32)**2))
        
        # Track initial ambient noise to adapt threshold dynamically
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
                if silence_start and (time.time() - silence_start >= silence_threshold) and len(audio_chunks) > 5:
                    print("[Silence detected. Processing Speech... ⚡]")
                    break
                if elapsed >= max_duration:
                    print("[Max duration reached. Processing Speech... ⚡]")
                    break

        if not audio_chunks:
            return ""

        recording = np.concatenate(audio_chunks, axis=0)

        # Gain Normalization: Boost low volume signals so faint mic input is clear
        max_val = np.max(np.abs(recording))
        if max_val > 50 and max_val < 18000:
            boost_factor = 22000.0 / float(max_val)
            recording = (recording.astype(np.float32) * boost_factor).clip(-32768, 32767).astype(np.int16)

        # Save to WAV file
        with wave.open(temp_wav, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(recording.tobytes())
            
        # Transcribe using SpeechRecognition
        recognizer = sr.Recognizer()
        recognizer.operation_timeout = 10.0
        with sr.AudioFile(temp_wav) as source:
            audio = recognizer.record(source)
            
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
            
        text_en = ""
        text_fr = ""
        
        # Pass 1: French language recognition
        try:
            text_fr = recognizer.recognize_google(audio, language="fr-FR").strip()
        except Exception:
            pass

        # Pass 2: English language recognition
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
