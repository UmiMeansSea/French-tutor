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

def speak_french(text, speed=1000):
    if not TTS_AVAILABLE:
        return
    if not text.strip():
        return
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

def listen_to_mic():
    if not VOICE_AVAILABLE:
        print("\n[Microphone Error: Voice input packages (sounddevice/SpeechRecognition) are missing.]")
        return ""

    temp_wav = os.path.abspath("temp_input.wav")
    duration = 5.0  # record for 5 seconds
    sample_rate = 16000
    
    try:
        print("\n[Listening... Speak in French or English (5 seconds)]")
        # Record audio using sounddevice (int16 numpy array)
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()  # Block until the recording is finished
        print("[Processing Speech...]")
        
        # Save to WAV file using built-in wave module (no wavio or scipy required)
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
