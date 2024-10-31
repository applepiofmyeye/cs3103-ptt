# app.py
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import threading
import socket
import subprocess
import os

app = Flask(__name__)
socketio = SocketIO(app)

# Configuration
TEACHER_IP = '10.249.217.20'
TEACHER_PORT = 59421
STUDENT_PORT = 62193

# Global state
current_streamer = None
stream_lock = threading.Lock()

class AudioStreamer:
    def __init__(self, student_id):
        self.student_id = student_id
        self.is_streaming = False
        self.gstreamer_process = None
        
    def send_student_id(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as id_socket:
            id_socket.settimeout(5)
            try:
                id_socket.bind(('0.0.0.0', STUDENT_PORT))
                id_socket.listen()
                print(f"Waiting for teacher connection to send ID: {self.student_id}")
                conn, addr = id_socket.accept()
                if addr[0] == TEACHER_IP:
                    conn.sendall(self.student_id.encode())
                    print(f"Sent student ID: {self.student_id}")
                conn.close()
                return True
            except Exception as e:
                print(f"Error sending student ID: {e}")
                return False

    def start_streaming(self):
        if self.is_streaming:
            return False
            
        # GStreamer pipeline for microphone capture and streaming
        gst_command = [
            'gst-launch-1.0', '-e',
            'pulsesrc', '!',
            'audioconvert', '!',
            'opusenc', '!',
            'oggmux', '!',
            'tcpclientsink',
            f'host={TEACHER_IP}',
            f'port={TEACHER_PORT}'
        ]
        
        try:
            if self.send_student_id():
                self.gstreamer_process = subprocess.Popen(gst_command)
                self.is_streaming = True
                return True
        except Exception as e:
            print(f"Error starting stream: {e}")
            return False
            
    def stop_streaming(self):
        if self.gstreamer_process:
            self.gstreamer_process.terminate()
            self.gstreamer_process = None
            self.is_streaming = False

@app.route('/')
def index():
    return render_template('./index.html')

@socketio.on('start_stream')
def handle_start_stream(data):
    global current_streamer
    
    with stream_lock:
        if current_streamer is not None:
            return {'success': False, 'message': 'Another student is currently streaming'}
            
        student_id = data.get('student_id')
        if not student_id:
            return {'success': False, 'message': 'Student ID is required'}
            
        current_streamer = AudioStreamer(student_id)
        if current_streamer.start_streaming():
            return {'success': True, 'message': 'Streaming started'}
        else:
            current_streamer = None
            return {'success': False, 'message': 'Failed to start streaming'}

@socketio.on('stop_stream')
def handle_stop_stream():
    global current_streamer
    
    with stream_lock:
        if current_streamer:
            current_streamer.stop_streaming()
            current_streamer = None
            return {'success': True, 'message': 'Streaming stopped'}
        return {'success': False, 'message': 'No active stream'}

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)