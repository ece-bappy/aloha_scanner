import cv2
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import time
from threading import Thread, Event

class PhotoScannerApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("1000x830")  # Increased height for status bar
        self.window.configure(bg="#f0f0f0")

        self.camera = None
        self.current_frame = None

        self.csv_data = []
        self.current_index = 0
        self.start_sl = 1

        self.is_running = False
        self.pause_event = Event()
        self.loading = False

        self.save_directory = os.path.expanduser("~")  # Default to user's home directory

        self.create_widgets()

        self.loading_label = ttk.Label(self.window, text="Initializing Camera...", font=("Helvetica", 16))
        self.loading_label.grid(row=0, column=0, columnspan=4, pady=20)

        self.set_status("Camera initializing")
        Thread(target=self.initialize_camera).start()

        self.window.mainloop()

    def initialize_camera(self):
        self.camera = cv2.VideoCapture(0)
        self.window.after(0, self.start_update)

    def start_update(self):
        self.loading_label.grid_forget()
        self.set_status("Ready")
        self.update()

    def create_widgets(self):
        # Camera feed
        self.canvas = tk.Canvas(self.window, width=640, height=480, bg="black")
        self.canvas.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        self.btn_load = ttk.Button(button_frame, text="Load List", command=self.load_csv)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_start = ttk.Button(button_frame, text="Start", command=self.start_capture)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_pause = ttk.Button(button_frame, text="Pause", command=self.pause_capture)
        self.btn_pause.pack(side=tk.LEFT, padx=5)

        self.btn_set_destination = ttk.Button(button_frame, text="Set Save Location", command=self.set_save_location)
        self.btn_set_destination.pack(side=tk.LEFT, padx=5)

        # Entry for interval and starting SL
        entry_frame = ttk.Frame(self.window)
        entry_frame.grid(row=3, column=0, columnspan=3, pady=10)

        ttk.Label(entry_frame, text="Interval (seconds):").pack(side=tk.LEFT, padx=5)
        self.entry_interval = ttk.Entry(entry_frame, width=10)
        self.entry_interval.insert(0, "40")
        self.entry_interval.pack(side=tk.LEFT, padx=5)

        ttk.Label(entry_frame, text="Start from SL:").pack(side=tk.LEFT, padx=5)
        self.entry_start_sl = ttk.Entry(entry_frame, width=10)
        self.entry_start_sl.insert(0, "1")
        self.entry_start_sl.pack(side=tk.LEFT, padx=5)

        # Label for current ID and countdown
        self.lbl_current_id = ttk.Label(self.window, text="Current ID: ", font=("Helvetica", 16))
        self.lbl_current_id.grid(row=4, column=0, columnspan=3, pady=10)

        self.lbl_countdown = ttk.Label(self.window, text="Time to next capture: ", font=("Helvetica", 16))
        self.lbl_countdown.grid(row=5, column=0, columnspan=3, pady=10)

        # Scrollable list for IDs
        self.scroll_frame = ttk.Frame(self.window)
        self.scroll_frame.grid(row=1, column=3, rowspan=5, padx=10, pady=10, sticky="nsew")

        self.listbox = tk.Listbox(self.scroll_frame, font=("Helvetica", 12), height=25, width=30)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.scroll_frame, orient="vertical", command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox.config(yscrollcommand=self.scrollbar.set)

        # Status bar
        self.status_bar = ttk.Label(self.window, text="Status: Ready", font=("Helvetica", 12), relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=6, column=0, columnspan=4, sticky="ew", pady=10)

    def set_status(self, status):
        self.status_bar.config(text=f"Status: {status}")

    def set_save_location(self):
        directory = filedialog.askdirectory()
        if directory:
            self.save_directory = directory
            messagebox.showinfo("Save Location", f"Files will be saved to: {self.save_directory}")

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            with open(file_path, 'r') as file:
                csv_reader = csv.DictReader(file)
                self.csv_data = list(csv_reader)
            self.listbox.delete(0, tk.END)  # Clear existing items
            for row in self.csv_data:
                self.listbox.insert(tk.END, row['ID'])
            messagebox.showinfo("CSV Loaded", f"Loaded {len(self.csv_data)} entries")
            self.set_status("Ready")

    def start_capture(self):
        if not self.csv_data:
            messagebox.showerror("Error", "Please load a CSV file first")
            return

        self.start_sl = int(self.entry_start_sl.get())
        self.current_index = self.start_sl - 1
        self.is_running = True
        self.pause_event.clear()
        self.set_status("Capturing")
        Thread(target=self.capture_loop).start()

    def pause_capture(self):
        self.is_running = False
        self.pause_event.set()
        self.set_status("Paused")

    def capture_loop(self):
        while self.is_running and self.current_index < len(self.csv_data):
            current_id = self.csv_data[self.current_index]['ID']
            self.lbl_current_id.config(text=f"Current ID: {current_id}")
            interval = int(self.entry_interval.get())
            for i in range(interval, 0, -1):
                if not self.is_running:
                    return
                self.lbl_countdown.config(text=f"Time to next capture: {i}s")
                time.sleep(1)

            if self.pause_event.is_set():
                return

            self.capture_photo()
            self.current_index += 1

        self.set_status("Finished")

    def capture_photo(self):
        if self.current_frame is not None:
            current_id = self.csv_data[self.current_index]['ID']
            filename = os.path.join(self.save_directory, f"{current_id}.jpg")
            cv2.imwrite(filename, cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR))
            self.lbl_current_id.config(text=f"Current ID: {current_id}")
            self.listbox.itemconfig(self.current_index, {'bg':'yellow'})

    def update(self):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.current_frame))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.window.after(10, self.update)

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoScannerApp(root, "ALOHA Image Capture System")