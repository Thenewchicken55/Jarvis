import io
import wave
import yaml
import tempfile
import queue
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
        self._queue = queue.Queue()
        self._engine_type = "none"
        self._init_engine()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _init_engine(self):
        engine = config["voice"]["tts_engine"]
        if engine == "edge_tts":
            try:
                import edge_tts
                self._engine_type = "edge_tts"
                return
            except ImportError:
                print("edge_tts not installed. Trying pyttsx3.")
        try:
            import pyttsx3
            self._engine_type = "pyttsx3"
        except ImportError:
            print("pyttsx3 not installed either. Text-to-speech disabled.")

    def _worker_loop(self):
        if self._engine_type == "pyttsx3":
            import pyttsx3
            engine = pyttsx3.init()
            while True:
                text = self._queue.get()
                if text is None:
                    break
                engine.say(text)
                engine.runAndWait()
        elif self._engine_type == "edge_tts":
            while True:
                text = self._queue.get()
                if text is None:
                    break
                self._speak_edge_tts(text)

    def speak(self, text):
        if self._engine_type != "none":
            self._queue.put(text)

    def _speak_edge_tts(self, text):
        import asyncio
        import edge_tts
        communicate = edge_tts.Communicate(text)
        asyncio.run(communicate.save(tempfile.mktemp(suffix=".mp3")))
        import subprocess
        subprocess.run(["start", tempfile.mktemp(suffix=".mp3")], shell=True)
