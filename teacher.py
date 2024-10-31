# https://chatgpt.com/share/671f6687-7a5c-8012-b50d-86b96712a293

import threading
import socket
import subprocess

TEACHER_IP = '10.249.217.20'
TEACHER_PORT = 59421
STUDENT_PORT = 62193

# Flag to track connection state
zero_connection = True
# Lock to prevent race condition between threads
zero_connection_lock = threading.Lock()


def gstreamer_pipeline():

    # GStreamer command
    #   -e           : flushing all data at the end
    #   fdsrc        : reads data from a file descriptor
    #   oggdemux     : demultiplexes audio and video stream
    #   opusdec      : decoder for Opus
    #   audioconvert : converts audio formats and sample rates
    #   autoaudiosink: automatically select output and play audio
    gst_command = "gst-launch-1.0 -e fdsrc ! oggdemux ! opusdec ! audioconvert ! autoaudiosink"

    # Start the GStreamer pipeline
    process = subprocess.Popen(gst_command, shell=True, stdin=subprocess.PIPE)

    return process


def process_data(conn, addr):
    print(f"Connected by {addr}")
    global zero_connection

    # >>> JUST ADDED THIS, DID NOT REALLY THINK OF ERROR CONTINGENCY <<<
    # "Ask" for student id
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as id_socket:
        # Set a timeout of 5 seconds
        id_socket.settimeout(5)
        try:
            # Connect to the student’s socket
            id_socket.connect((addr[0], STUDENT_PORT))
            # Listen for data (student should send over student ID)
            data = id_socket.recv(1024)
            print("Talking student:", data.decode())
        except Exception as e:
            print("Could not get student ID:", e)
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # Start GStreamer pipeline
    gstreamer_process = gstreamer_pipeline()
    print("GStreamer pipeline started.")

    # Pipe data from the TCP connection to GStreamer
    try:
        while True:
            # Read data from TCP buffer
            data = conn.recv(4096)
            # If connection closed by client
            if not data:
                break
            # Write data to the GStreamer process stdin
            gstreamer_process.stdin.write(data)
            gstreamer_process.stdin.flush()
    except Exception as e:
        print(f"Error while piping data: {e}")
    finally:
        gstreamer_process.terminate()
        print("GStreamer pipeline terminated.")

    # Blocks until the lock is acquired; automatically releases the lock upon exiting the scope.
    with zero_connection_lock:
        zero_connection = True


def process_incoming_connection(s):
    global zero_connection

    while True:

        # Blocks until a connection is accepted
        conn, addr = s.accept()

        # Blocks execution until the lock is acquired; automatically releases the lock upon exiting the scope.
        with zero_connection_lock:
            # Process data
            if zero_connection:
                # Update flag
                zero_connection = False
                # Circumvent pass-by-ref
                connection, address = conn, addr
                # Run process_data() in a new thread
                thread_process_data = threading.Thread(target=process_data, args=(connection, address))
                # Start the thread
                thread_process_data.start()
                continue

        # Immediately close the connection
        conn.close()
        print(f"Connection from {addr} rejected: active connection already exists.")


def run_server():
    # Create TCP socket that auto close upon out of scope
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Bind socket
        s.bind((TEACHER_IP, TEACHER_PORT))
        # Listen
        s.listen()
        print(f"Listening on {TEACHER_IP}:{TEACHER_PORT}...")
        # Run process_incoming_connection() in a new thread
        thread_process_incoming_connection = threading.Thread(target=process_incoming_connection, args=(s,))
        # Start the thread
        thread_process_incoming_connection.start()
        # Wait for the thread to complete
        thread_process_incoming_connection.join()


if __name__ == "__main__":
    run_server()
