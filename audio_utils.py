import io
import wave
import yaml
import tempfile
import threading
import sounddevice as sd
import numpy as np

with open('config.yaml') as f:
    config = yaml.safe_load(f)

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'


def record_audio(duration=None, fs=SAMPLE_RATE):
    if duration:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=CHANNELS, dtype=DTYPE)
        sd.wait()
    else:
        sd.wait()
        recording = sd.rec(int(10 * fs), samplerate=fs, channels=CHANNELS, dtype=DTYPE)
        sd.wait()
    return recording.flatten()


def audio_to_wav_bytes(audio_data, fs=SAMPLE_RATE):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(audio_data.tobytes())
    buf.seek(0)
    return buf


class SpeechToText:
    def __init__(self):
        engine = config["voice"]["stt_engine"]
        if engine == "whisper":
            self._init_whisper()
        else:
            self._init_speech_recognition()

    def _init_speech_recognition(self):
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.engine = "speech_recognition"
        except ImportError:
            print("speech_recognition not installed. Falling back to whisper.")
            self._init_whisper()

    def _init_whisper(self):
        try:
            from faster_whisper import WhisperModel
            self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            self.engine = "whisper"
        except ImportError:
            print("faster-whisper not installed. Trying speech_recognition...")
            self._init_speech_recognition()

    def transcribe(self, audio_data, fs=SAMPLE_RATE):
        if self.engine == "whisper":
            return self._transcribe_whisper(audio_data, fs)
        else:
            return self._transcribe_sr(audio_data, fs)

    def _transcribe_whisper(self, audio_data, fs):
        audio_float = audio_data.astype(np.float32) / 32768.0
        segments, _ = self.whisper_model.transcribe(audio_float, beam_size=1)
        return " ".join(seg.text for seg in segments)

    def _transcribe_sr(self, audio_data, fs):
        import speech_recognition as sr
        wav_bytes = audio_to_wav_bytes(audio_data, fs)
        with sr.AudioFile(wav_bytes) as source:
            audio = self.recognizer.record(source)
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""

    def listen_and_transcribe(self, duration=None):
        audio = record_audio(duration)
        return self.transcribe(audio)


class TextToSpeech:
    def __init__(self):
        self._lock = threading.Lock()
        engine = config["voice"]["tts_engine"]
        if engine == "edge_tts":
            self._init_edge_tts()
        else:
            self._init_pyttsx3()

    def _init_pyttsx3(self):
        try:
            import pyttsx3
            self.engine_tts = pyttsx3.init()
            self.engine = "pyttsx3"
        except ImportError:
            print("pyttsx3 not installed. Falling back to edge_tts.")
            self._init_edge_tts()

    def _init_edge_tts(self):
        try:
            import edge_tts
            self.engine = "edge_tts"
        except ImportError:
            print("edge_tts not installed either. Text-to-speech disabled.")
            self.engine = "none"

    def speak(self, text):
        if self.engine == "pyttsx3":
            self._speak_pyttsx3(text)
        elif self.engine == "edge_tts":
            self._speak_edge_tts(text)

    def _speak_pyttsx3(self, text):
        with self._lock:
            self.engine_tts.say(text)
            self.engine_tts.runAndWait()

    def _speak_edge_tts(self, text):
        import asyncio
        import edge_tts
        communicate = edge_tts.Communicate(text)
        asyncio.run(communicate.save(tempfile.mktemp(suffix=".mp3")))
        import subprocess
        subprocess.run(["start", tempfile.mktemp(suffix=".mp3")], shell=True)
