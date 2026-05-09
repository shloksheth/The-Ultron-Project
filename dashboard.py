from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import psutil
import threading
import time
from ultron_brain import UltronBrain
from voice_service import VoiceService
import os

app = Flask(__name__)
socketio = SocketIO(app)
brain = UltronBrain()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('command')
def handle_command(data):
    user_input = data['message']
    response = brain.chat(user_input)
    emit('command_result', {'response': response})
    emit('log', {'message': f"Ultron: {response}", 'type': 'ai'})

def stats_thread():
    while True:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        socketio.emit('stats', {'cpu': cpu, 'mem': mem})
        time.sleep(2)

def run_server():
    socketio.run(app, port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    threading.Thread(target=stats_thread, daemon=True).start()
    run_server()
