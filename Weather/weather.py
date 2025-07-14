import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading

def center_window(window, width, height):
    root.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - (width // 2)
    y = root.winfo_y() + (root.winfo_height() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

def start_weather_forecast():
    city = entry.get().strip()
    if not city:
        messagebox.showerror("Missing Input", "Please enter a city name.", parent=root)
        return

    def process():
        steps = [
            "Searching Location...",
            "Analyzing Cloud Patterns...",
            "Measuring Wind Speed...",
            "Gathering Satellite Data...",
            "Checking Temperature Trends...",
            "Finalizing Forecast..."
        ]

        progress_win = tk.Toplevel(root)
        progress_win.title("AI Weather Forecasting")
        center_window(progress_win, 400, 130)
        progress_win.transient(root)
        progress_win.grab_set()

        progress_label = tk.Label(progress_win, text="Initializing...", font=("Arial", 11))
        progress_label.pack(pady=10)

        progress = ttk.Progressbar(progress_win, orient=tk.HORIZONTAL, length=350, mode='determinate')
        progress.pack(pady=10)

        total_steps = len(steps)
        for i in range(100):
            time.sleep(0.04)
            progress["value"] = i + 1
            step_index = (i * total_steps) // 100
            if step_index < total_steps:
                progress_label.config(text=steps[step_index])
            progress_win.update()

        progress_win.destroy()
        root.after(100, lambda: messagebox.showinfo("Forecast Ready", f"Just look outside ☁️🌦️", parent=root))

    threading.Thread(target=process).start()

# GUI setup
root = tk.Tk()
root.title("AI Weather Forecasting")
root.geometry("400x200")

heading = tk.Label(root, text="Enter your city name:", font=("Arial", 14))
heading.pack(pady=20)

entry = tk.Entry(root, font=("Arial", 12), justify="center")
entry.pack(pady=5)

forecast_button = tk.Button(root, text="Get Forecast", font=("Arial", 12), command=start_weather_forecast)
forecast_button.pack(pady=20)

root.mainloop()
