import os
import threading
import queue
import time
import speech_recognition as sr
from faster_whisper import WhisperModel
import pyttsx3

class VoiceService:
    def __init__(self, model_size="base", wake_word="ultron"):
        self.wake_word = wake_word.lower()
        # Initialize Faster-Whisper
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        # Initialize TTS
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)
            self.engine.setProperty('rate', 180)
        except Exception as e:
            print(f"Warning: TTS initialization failed: {e}")
            self.engine = None
        
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            print(f"Warning: Microphone not found: {e}")
            self.microphone = None
        
        self.command_queue = queue.Queue()
        self.is_listening = False

    def speak(self, text):
        print(f"Ultron: {text}")
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()

    def listen_loop(self):
        if not self.microphone:
            print("Error: No microphone available for listening.")
            return

        self.is_listening = True
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening for wake word 'Ultron'...")
            
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    with open("temp_audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    
                    segments, info = self.model.transcribe("temp_audio.wav", beam_size=5)
                    text = "".join([segment.text for segment in segments]).strip().lower()
                    
                    if self.wake_word in text:
                        print(f"Wake word detected: {text}")
                        command = text.split(self.wake_word)[-1].strip()
                        if not command:
                            self.speak("How can I help you?")
                            audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                            with open("temp_audio.wav", "wb") as f:
                                f.write(audio.get_wav_data())
                            segments, _ = self.model.transcribe("temp_audio.wav", beam_size=5)
                            command = "".join([segment.text for segment in segments]).strip().lower()
                        
                        if command:
                            print(f"Detected command: {command}")
                            self.command_queue.put(command)
                            
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"Error in listen loop: {e}")
                    continue

    def start(self):
        self.thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_listening = False
        if hasattr(self, 'thread'):
            self.thread.join()

if __name__ == "__main__":
    service = VoiceService()
