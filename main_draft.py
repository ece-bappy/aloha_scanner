import cv2
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import time
from threading import Thread, Event

class PhotoScannerApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        self.camera = cv2.VideoCapture(0)
        self.current_frame = None

        self.csv_data = []
        self.current_index = 0
        self.start_sl = 1

        self.is_running = False
        self.pause_event = Event()

        self.create_widgets()

        self.update()
        self.window.mainloop()

    def create_widgets(self):
        # Camera feed
        self.canvas = tk.Canvas(self.window, width=640, height=480)
        self.canvas.grid(row=0, column=0, columnspan=6, padx=10, pady=10)

        # Scrollable listbox for IDs
        self.listbox_frame = tk.Frame(self.window)
        self.listbox_frame.grid(row=0, column=6, rowspan=3, padx=10, pady=10, sticky='ns')

        self.scrollbar = tk.Scrollbar(self.listbox_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(self.listbox_frame, height=25, yscrollcommand=self.scrollbar.set, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        self.scrollbar.config(command=self.listbox.yview)

        # Buttons
        self.btn_load = tk.Button(self.window, text="Load List", command=self.load_csv)
        self.btn_load.grid(row=1, column=0, padx=10, pady=10)

        self.btn_start = tk.Button(self.window, text="Start", command=self.start_capture)
        self.btn_start.grid(row=1, column=1, padx=10, pady=10)

        self.btn_pause = tk.Button(self.window, text="Pause", command=self.pause_capture)
        self.btn_pause.grid(row=1, column=2, padx=10, pady=10)

        # Entry for interval
        tk.Label(self.window, text="Interval (seconds):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.entry_interval = tk.Entry(self.window)
        self.entry_interval.insert(0, "40")
        self.entry_interval.grid(row=2, column=1, padx=10, pady=5)

        # Entry for starting SL
        tk.Label(self.window, text="Start from SL:").grid(row=2, column=2, padx=10, pady=5, sticky="e")
        self.entry_start_sl = tk.Entry(self.window)
        self.entry_start_sl.insert(0, "1")
        self.entry_start_sl.grid(row=2, column=3, padx=10, pady=5)

        # Label for current ID
        self.lbl_current_id = tk.Label(self.window, text="Current ID: ", font=("Helvetica", 16))
        self.lbl_current_id.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        # Label for countdown
        self.lbl_countdown = tk.Label(self.window, text="Time to next capture: ", font=("Helvetica", 16))
        self.lbl_countdown.grid(row=3, column=3, columnspan=3, padx=10, pady=10)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            with open(file_path, 'r') as file:
                csv_reader = csv.DictReader(file)
                self.csv_data = list(csv_reader)

                # Clear the Listbox
                self.listbox.delete(0, tk.END)

                # Populate Listbox with IDs
                for row in self.csv_data:
                    self.listbox.insert(tk.END, row['ID'])

            messagebox.showinfo("CSV Loaded", f"Loaded {len(self.csv_data)} entries")

    def start_capture(self):
        if not self.csv_data:
            messagebox.showerror("Error", "Please load a CSV file first")
            return

        self.start_sl = int(self.entry_start_sl.get())
        self.current_index = self.start_sl - 1
        self.is_running = True
        self.pause_event.clear()
        Thread(target=self.capture_loop).start()

    def pause_capture(self):
        self.is_running = False
        self.pause_event.set()

    def capture_loop(self):
        while self.is_running and self.current_index < len(self.csv_data):
            # Update the current ID before the countdown
            current_id = self.csv_data[self.current_index]['ID']
            self.lbl_current_id.config(text=f"Current ID: {current_id}")

            # Highlight the current ID in the Listbox
            self.listbox.selection_clear(0, tk.END)  # Clear previous selection
            self.listbox.selection_set(self.current_index)  # Highlight current ID
            self.listbox.activate(self.current_index)  # Ensure the selection is visible

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

    def capture_photo(self):
        if self.current_frame is not None:
            current_id = self.csv_data[self.current_index]['ID']
            filename = f"{current_id}.jpg"
            cv2.imwrite(filename, self.current_frame)
            self.lbl_current_id.config(text=f"Current ID: {current_id}")

    def update(self):
        ret, frame = self.camera.read()
        if ret:
            self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.current_frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.window.after(10, self.update)

if __name__ == "__main__":
    PhotoScannerApp(tk.Tk(), "Photo Scanner System")
