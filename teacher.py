# https://chatgpt.com/share/671f6687-7a5c-8012-b50d-86b96712a293

import threading
import socket
import subprocess

TEACHER_IP = '192.168.1.59'
TEACHER_PORT = 59421
STUDENT_PORT = 62193
STUDENT_ID_PORT = 62194

# Dictionary to store active student connections WHAT DOES THIS DO?

active_students = {}
active_students_lock = threading.Lock()

def gstreamer_pipeline():
    # GStreamer command with more explicit pipeline
    gst_command = [
        'gst-launch-1.0',
        '-v',  # Add verbose output
        'fdsrc',
        '!',
        'oggdemux',
        '!',
        'opusdec',
        '!',
        'audioconvert',
        '!',
        'audioresample',
        '!',
        'autoaudiosink'
    ]
    
    print(f"Starting GStreamer pipeline with command: {' '.join(gst_command)}")
    
    process = subprocess.Popen(
        gst_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Start a thread to monitor GStreamer output
    def monitor_output():
        while True:
            output = process.stderr.readline()
            if not output:
                break
            print(f"GStreamer: {output.decode().strip()}")
    
    threading.Thread(target=monitor_output, daemon=True).start()
    
    return process

def process_data(conn, addr, student_id):
    print(f"Processing audio from student {student_id} at {addr}")
    
    # Start GStreamer pipeline
    gstreamer_process = gstreamer_pipeline()
    print("GStreamer pipeline started.")

    # Pipe data from the TCP connection to GStreamer
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                print("No more data received from client")
                break
            print(f"Received {len(data)} bytes of audio data")
            gstreamer_process.stdin.write(data)
            gstreamer_process.stdin.flush()
    except Exception as e:
        print(f"Error while piping data: {e}")
    finally:
        gstreamer_process.terminate()
        print("GStreamer pipeline terminated.")
        
        # Remove student from active connections
        with active_students_lock:
            if student_id in active_students:
                del active_students[student_id]
                print(f"Removed student {student_id} from active connections")
                
def process_incoming_connection(s):
    while True:
        conn, addr = s.accept()
        
        # Check if this is a known student
        student_id = None
        print(f"Active students: {active_students}")
        with active_students_lock:
            for sid, ip in active_students.items():
                if ip == addr[0]:
                    student_id = sid
                    break
        
        if student_id:
            # Only process if we found a valid student
            print(f"Processing audio from student {student_id} at {addr}")
            thread_process_data = threading.Thread(
                target=process_data, 
                args=(conn, addr, student_id)
            )
            thread_process_data.start()
        else:
            # Unknown connection, reject it
            conn.close()
            print(f"Connection from {addr} rejected: unknown student")

def handle_student_id():
    """Handle incoming student ID connections (Student ID Port)"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as id_socket:
        id_socket.bind((TEACHER_IP, STUDENT_ID_PORT))
        id_socket.listen()
        print(f"Listening for student IDs on {TEACHER_IP}:{STUDENT_ID_PORT}...")
        
        while True:
            conn, addr = id_socket.accept()
            try:
                student_id = conn.recv(1024).decode()
                print(f"Received student ID: {student_id} from {addr}")
                
                # Store student info
                with active_students_lock:
                    active_students[student_id] = addr[0]
                
                # Send acknowledgment
                conn.sendall("OK".encode())
                conn.close()
                print(f"Registered student {student_id}")
               
            except Exception as e:
                print(f"Error receiving student ID: {e}")
                conn.close()
def run_server():
    # Start thread for handling student IDs
    id_thread = threading.Thread(target=handle_student_id)
    id_thread.daemon = True
    id_thread.start()

     # Handle audio connections
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((TEACHER_IP, TEACHER_PORT))
        s.listen()
        print(f"Listening for audio on {TEACHER_IP}:{TEACHER_PORT}...")
        
        thread_process_incoming_connection = threading.Thread(
            target=process_incoming_connection, 
            args=(s,)
        )
        thread_process_incoming_connection.start()
        thread_process_incoming_connection.join() # Wait for the thread to complete
    


if __name__ == "__main__":
    run_server()
