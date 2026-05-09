import threading
import time
import queue
from dashboard import app, socketio, brain
from voice_service import VoiceService
from automation import run_automation
from credentials_manager import CredentialManager
import psutil

class UltronSystem:
    def __init__(self):
        self.voice = VoiceService()
        self.creds_manager = CredentialManager()
        
    def start_voice_listener(self):
        self.voice.start()
        threading.Thread(target=self._process_commands, daemon=True).start()

    def _process_commands(self):
        while True:
            try:
                command = self.voice.command_queue.get(timeout=1)
                socketio.emit('log', {'message': f"Voice: {command}", 'type': 'voice'})
                
                response = brain.chat(command)
                socketio.emit('command_result', {'response': response})
                socketio.emit('log', {'message': f"Ultron: {response}", 'type': 'ai'})
                
                # Check for actions in response
                if "[ACTION:" in response:
                    # Very simple action parser for demo
                    if "deltamath" in command:
                        self._handle_deltamath(command)
                
                self.voice.speak(response.split("[ACTION:")[0].strip())
                
            except queue.Empty:
                continue

    def _handle_deltamath(self, command):
        creds = self.creds_manager.get_creds("deltamath")
        if not creds:
            socketio.emit('log', {'message': "Deltamath credentials missing. Please provide them.", 'type': 'error'})
            self.voice.speak("I don't have your Delta Math credentials yet.")
            return
        
        socketio.emit('browser_update', {'status': 'OPENING DELTAMATH...'})
        threading.Thread(target=run_automation, args=(creds, socketio), daemon=True).start()

def stats_thread():
    while True:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        socketio.emit('stats', {'cpu': cpu, 'mem': mem})
        time.sleep(2)

if __name__ == "__main__":
    system = UltronSystem()
    system.start_voice_listener()
    
    threading.Thread(target=stats_thread, daemon=True).start()
    
    print("Ultron System starting on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
