import threading
import socket
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

TEACHER_IP = '192.168.1.59'
TEACHER_PORT = 59421
STUDENT_IP = '192.168.1.59'
STUDENT_PORT = 62193
STUDENT_ID_PORT = 62194 

class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Voice Chat")
        self.root.geometry("400x300")
        
        self.gstreamer_process = None
        
        # Student ID input frame
        id_frame = ttk.LabelFrame(root, text="Student Identification", padding="10")
        id_frame.pack(fill="x", padx=10, pady=5)
        
        # Student ID entry
        self.student_id = tk.StringVar()
        ttk.Label(id_frame, text="Student ID:").pack(side="left", padx=5)
        self.id_entry = ttk.Entry(id_frame, textvariable=self.student_id)
        self.id_entry.pack(side="left", padx=5)
        
        # Submit button
        self.submit_btn = ttk.Button(id_frame, text="Submit", command=self.submit_id)
        self.submit_btn.pack(side="left", padx=5)
        
        # Push to talk frame
        ptt_frame = ttk.LabelFrame(root, text="Push to Talk", padding="10")
        ptt_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Push to talk button
        self.ptt_btn = ttk.Button(ptt_frame, text="Push to Talk")
        self.ptt_btn.pack(expand=True, pady=20)
        self.ptt_btn.bind('<ButtonPress-1>', self.start_talking)
        self.ptt_btn.bind('<ButtonRelease-1>', self.stop_talking)
        
        # Initially disable PTT button until ID is submitted
        self.ptt_btn.state(['disabled'])
        
        # Status label
        self.status_var = tk.StringVar(value="Please submit your Student ID")
        self.status_label = ttk.Label(root, textvariable=self.status_var)
        self.status_label.pack(pady=10)
    def submit_id(self):
        if not self.student_id.get().strip():
            messagebox.showerror("Error", "Please enter a Student ID")
            return
            
        try:
            # Try to connect directly to teacher to send ID
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as id_socket:
                try:
                    print(f"Sending student ID: {self.student_id.get()}")
                    id_socket.settimeout(5)
                    id_socket.connect((TEACHER_IP, STUDENT_ID_PORT))
                    id_socket.sendall(self.student_id.get().encode())
                    
                    # Wait for acknowledgment
                    response = id_socket.recv(1024).decode()
                    if response != "OK":
                        raise Exception("Registration not acknowledged by teacher")
                    
                    # If successful, enable PTT
                    self.submit_btn.state(['disabled'])
                    self.id_entry.state(['disabled'])
                    self.ptt_btn.state(['!disabled'])
                    self.status_var.set("ID submitted successfully. Ready to talk.")
                    
                except Exception as e:
                    raise Exception(f"Could not connect to teacher: {str(e)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit ID: {str(e)}")
            self.reset_id_submission()
    def reset_id_submission(self):
        self.submit_btn.state(['!disabled'])
        self.id_entry.state(['!disabled'])
        self.ptt_btn.state(['disabled'])
        self.status_var.set("Please submit your Student ID")

    def start_talking(self, event):
        try:
            # Build the GStreamer command
            gst_command = [
                'gst-launch-1.0',
                '-v',  # Add verbose output
                'autoaudiosrc',
                '!',
                'audioconvert',
                '!',
                'audioresample',  # Add this to handle sample rate conversion
                '!',
                'opusenc',
                '!',
                'oggmux',
                '!',
                'tcpclientsink',
                f'host={TEACHER_IP}',
                f'port={TEACHER_PORT}'
            ]
            
            print(f"Starting GStreamer with command: {' '.join(gst_command)}")
            
            # Start GStreamer process with pipe for stderr
            self.gstreamer_process = subprocess.Popen(
                gst_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
            # Start a thread to monitor the process output
            def monitor_output():
                while self.gstreamer_process:
                    output = self.gstreamer_process.stderr.readline()
                    if output:
                        print(f"GStreamer: {output.decode().strip()}")
                    
            threading.Thread(target=monitor_output, daemon=True).start()
            
            self.status_var.set("Broadcasting audio...")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start audio: {str(e)}")
            print(f"Error starting GStreamer: {str(e)}")
    
    def stop_talking(self, event):
        if self.gstreamer_process:
            self.gstreamer_process.terminate()
            self.gstreamer_process = None
            self.status_var.set("Ready to talk")

def main():
    root = tk.Tk()
    app = StudentApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()