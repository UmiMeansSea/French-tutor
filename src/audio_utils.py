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
    
    style_clean = str(mentor_style).lower()
    # Mentor Voice Speed Tuning (Leda / Charon / Gacrux presets)
    if "derek" in style_clean or "coach" in style_clean or "strict" in style_clean:
        # Derek (Charon preset): Deep, serious, slow & deliberate
        speed = int(speed * 0.88)
    elif "alice" in style_clean or "storyteller" in style_clean or "story" in style_clean:
        # Alice (Gacrux preset): Warm, mature, expressive storytelling
        speed = int(speed * 0.96)
    else:
        # Clara (Leda preset): Light, carefree, youthful & soothing
        speed = int(speed * 1.05)

    temp_file = os.path.abspath("temp_response.mp3")
    try:
        # Create TTS MP3
        tts = gTTS(text=text, lang='fr')
        tts.save(temp_file)
        
        # Play via Windows MCI (winmm.dll)
        winmm = ctypes.windll.winmm
        
        # Open command
        open_command = f'open "{temp_file}" type mpegvideo alias mymp3'
        winmm.mciSendStringW(open_command, None, 0, 0)
        
        # Set speed
        winmm.mciSendStringW(f'set mymp3 speed {speed}', None, 0, 0)
        
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

def listen_to_mic(silence_threshold=2.8, sample_rate=16000, max_duration=60.0):
    if not VOICE_AVAILABLE:
        print("\n[Microphone Error: Voice input packages (sounddevice/SpeechRecognition) are missing.]")
        return ""

    temp_wav = os.path.abspath("temp_input.wav")
    print("\n[Listening... Speak freely. Pausing for ~3 seconds finishes your turn]")
    
    audio_chunks = []
    silence_start = None
    start_time = time.time()
    SILENCE_RMS_THRESHOLD = 300  # Silence detection energy threshold

    def callback(indata, frames, time_info, status):
        nonlocal silence_start
        audio_chunks.append(indata.copy())
        rms = np.sqrt(np.mean(indata.astype(np.float32)**2))
        
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
                    print("[Silence detected. Processing Speech...]")
                    break
                if elapsed >= max_duration:
                    print("[Max duration reached. Processing Speech...]")
                    break

        if not audio_chunks:
            return ""

        recording = np.concatenate(audio_chunks, axis=0)

        # Save to WAV file using built-in wave module
        with wave.open(temp_wav, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit is 2 bytes
            wf.setframerate(sample_rate)
            wf.writeframes(recording.tobytes())
            
        # Transcribe using SpeechRecognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            audio = recognizer.record(source)
            
        # Cleanup temp WAV file immediately
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
            
        # Attempt French transcription first
        try:
            text = recognizer.recognize_google(audio, language="fr-FR")
            return text
        except sr.UnknownValueError:
            try:
                text = recognizer.recognize_google(audio, language="en-US")
                return text
            except sr.UnknownValueError:
                print("[Speech not recognized. Please try again.]")
                return ""
    except Exception as e:
        print(f"[Microphone Error: {e}]")
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
        return ""
