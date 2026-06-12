import threading
import time
import queue
import sys
import yaml
import numpy as np
import sounddevice as sd

from llm_chains import create_llm_chain
from audio_utils import SpeechToText, TextToSpeech, SAMPLE_RATE
from keyboard_agent import KeyboardAgent


class Jarvis:
    def __init__(self):
        with open('config.yaml') as f:
            self.config = yaml.safe_load(f)

        self.llm_chain = create_llm_chain()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.kb = KeyboardAgent()

        self.ptt_key = self.config["voice"]["push_to_talk_key"]
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.audio_chunks = []
        self.running = True

    def audio_callback(self, indata, frames, time_info, status):
        if self.is_recording:
            self.audio_queue.put(indata.copy())

    def process_speech(self, audio_data):
        if len(audio_data) < SAMPLE_RATE * 0.3:
            return

        print("\nTranscribing...")
        text = self.stt.transcribe(audio_data, SAMPLE_RATE)
        if not text.strip():
            print("No speech detected")
            return

        print(f"You: {text}")
        print("Thinking...")
        response = self.llm_chain.run(text)
        print(f"Jarvis: {response}")

        clean_response = self.kb.execute_response(response)

        if self.tts.engine != "none":
            threading.Thread(target=self.tts.speak, args=(clean_response,), daemon=True).start()

    def on_press(self, e):
        if not self.is_recording:
            self.is_recording = True
            self.audio_chunks = []
            print(f"\nListening...")

    def on_release(self, e):
        if self.is_recording:
            self.is_recording = False
            print("Processing...")
            while not self.audio_queue.empty():
                self.audio_chunks.append(self.audio_queue.get_nowait())
            if self.audio_chunks:
                audio = np.concatenate(self.audio_chunks).flatten()
                threading.Thread(target=self.process_speech, args=(audio,), daemon=True).start()

    def run(self):
        try:
            import keyboard
        except ImportError:
            print("keyboard library required. Install: pip install keyboard")
            sys.exit(1)

        keyboard.on_press_key(self.ptt_key, self.on_press)
        keyboard.on_release_key(self.ptt_key, self.on_release)

        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='int16',
            callback=self.audio_callback,
        )
        stream.start()

        print(f"Jarvis ready. Hold '{self.ptt_key}' to talk, release to process.")
        print("Press Ctrl+C to exit.\n")

        try:
            keyboard.wait()
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop()
            stream.close()
            print("\nGoodbye.")


if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.run()
