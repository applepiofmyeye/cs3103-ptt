import threading
import socket
import subprocess

TEACHER_IP = '192.168.18.67'
TEACHER_PORT = 59421
STUDENT_IP = '192.168.18.67'
STUDENT_PORT = 62193

# >>> JUST ADDED THIS, DID NOT REALLY THINK OF ERROR CONTINGENCY <<<
def send_student_id(student_id):
    # Create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as id_socket:
        # Bind to the server IP and port
        id_socket.bind((STUDENT_IP, STUDENT_PORT))
        # Set a timeout of 5 seconds
        id_socket.settimeout(5)
        # Listen for incoming connections
        id_socket.listen()
        print("Waiting for a connection...")

        # Accept a connection
        while True:
            conn, addr = id_socket.accept()
            # Check if the connection is from the teacher's IP
            if addr[0] == TEACHER_IP:
                print(f"Connection accepted from {addr}")
                # Send student_id
                conn.sendall(student_id.encode())
                print("Sent student ID:", student_id)
                # Close the connection after sending
                conn.close()
                break
            else:
                print(f"Connection from unauthorized IP: {addr}")
                conn.close()

def start_gstreamer():

    # Build the GStreamer command
    gst_command = [
        'gst-launch-1.0',
        '-e',
        'autoaudiosrc',
        '!',
        'audioconvert',
        '!',
        'opusenc',
        '!',
        'oggmux',
        '!',
        'tcpclientsink',
        f'host={TEACHER_IP}',
        f'port={TEACHER_PORT}'
    ]

    # Run the GStreamer command
    try:
        print(f"Starting GStreamer to stream audio to {TEACHER_IP}:{TEACHER_PORT}...")
        subprocess.run(gst_command)
    except KeyboardInterrupt:
        print("Streaming stopped.")

def main():

    # Pass from GUI
    student_id = 'AXXXXXXXR'

    # Run process_incoming_connection() in a new thread
    thread_gstreamer = threading.Thread(target=start_gstreamer)
    thread_student_id = threading.Thread(target=send_student_id, args=(student_id,))

    # Start the thread
    thread_gstreamer.start()
    thread_student_id.start()
    
    # Wait for the thread to complete
    thread_student_id.join()
    thread_gstreamer.join()

if __name__ == "__main__":
    main()

