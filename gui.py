# gui.py

import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gcode_parser import parse_gcode, extract_movements
from time_calculator import calculate_time, DEFAULT_SETTINGS

class GCodeAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("G-Code Analyzer")
        self.geometry("800x600")
        self.settings = DEFAULT_SETTINGS.copy()

        self.create_widgets()

    def create_widgets(self):
        self.open_button = tk.Button(self, text="Open G-Code File", command=self.open_file)
        self.open_button.pack()

        self.settings_button = tk.Button(self, text="Settings", command=self.open_settings)
        self.settings_button.pack()

        self.result_label = tk.Label(self, text="")
        self.result_label.pack()

        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("G-Code files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'r') as file:
                gcode = file.read()

            lines = parse_gcode(gcode)
            total_time = calculate_time(lines, self.settings)
            self.display_time(total_time)

            movements = extract_movements(lines)
            self.plot_movements(movements)

    def display_time(self, total_time):
        minutes = int(total_time // 60)
        seconds = total_time % 60
        self.result_label.config(text=f"Estimated time to complete the program: {minutes} minutes and {seconds:.2f} seconds")

    def plot_movements(self, movements):
        fig, ax = plt.subplots()
        for move in movements:
            start, end = move
            ax.plot([start[0], end[0]], [start[1], end[1]], 'b-')

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("Tool Path")
        ax.axis('equal')

        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")

        labels = {
            "RAPID_SPEED": "Rapid Speed (mm/min):",
            "MAX_FEED_RATE": "Max Feed Rate (mm/min):",
            "ACCELERATION": "Acceleration (mm/s²):",
            "PALLET_CHANGE_TIME": "Pallet Change Time (seconds):",
            "M143_TIME": "M143 Time (seconds):",
            "M142_TIME": "M142 Time (seconds):",
            "M9_TIME": "M9 Time (seconds):",
            "M05_TIME": "M05 Time (seconds):"
        }

        for idx, (key, label) in enumerate(labels.items()):
            tk.Label(settings_window, text=label).grid(row=idx, column=0, padx=10, pady=5)
            entry = tk.Entry(settings_window)
            entry.insert(0, str(self.settings[key]))
            entry.grid(row=idx, column=1, padx=10, pady=5)
            entry.bind("<FocusOut>", lambda e, k=key, e2=entry: self.update_setting(k, e2))

    def update_setting(self, key, entry):
        try:
            self.settings[key] = float(entry.get())
        except ValueError:
            messagebox.showerror("Invalid input", f"Please enter a valid number for {key}.")

