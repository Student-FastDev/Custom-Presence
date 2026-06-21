import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pypresence import Presence
import time
import threading
import asyncio
import io
from datetime import datetime
import sys
import ctypes
import re
import json
import os
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageTk
from PIL import Image, ImageDraw
import math

CACHE_FILE = "cache.json"
file_background = "background_task.png"

def save_cache(data, script_content=None):
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        cache_data = {"inputs": data}
        if script_content:
            cache_data["script"] = script_content
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=4)
        print(f"Cache cleared and saved to: {CACHE_FILE}")

    except Exception as e:
        print(f"Error saving cache: {e}")

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
                inputs = cache_data.get("inputs", {})
                script_content = cache_data.get("script", "")
                return {"inputs": inputs, "script": script_content}
        except Exception as e:
            print(f"Error loading cache: {e}")
    return {"inputs": {}, "script": ""} 

def load_png_image_from_file(file_path):
    image = Image.open(file_path)
    image = image.resize((20, 15))
    image = image.convert("RGBA")
    pixels = image.load()
    for i in range(image.width):
        for j in range(image.height):
            r, g, b, a = pixels[i, j]
            if a > 0:
                pixels[i, j] = (255, 255, 255, a)

    return image

class OutputCapture(io.StringIO):
    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()

    def write(self, *args):
        with self.lock:
            output = ' '.join(map(str, args))
            super().write(output + '\n')
            sys.stdout.write(output + '\n')

    def read_latest_line(self):
        with self.lock:
            lines = self.getvalue().strip().split("\n")
            return lines[-1] if lines else ""

    def clear(self):
        with self.lock:
            self.seek(0)
            self.truncate(0)


class CustomLibrary:
    @staticmethod
    def get_time():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def generate_levels(count):
        return [f"Level {i+1}" for i in range(count)]

    @staticmethod
    def generate_number(start, end):
        import random
        return random.randint(start, end)

class CustomRichPresenceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Custom Discord Rich Presence")
        self.rpc = None
        self.running = False
        self.script_thread = None
        self.output_capture = OutputCapture()
        self.cached_data = load_cache()
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(6, weight=1)
        self.root.attributes("-alpha", 0)
        app_info_frame = ctk.CTkFrame(root, corner_radius=10)
        app_info_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        app_info_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(app_info_frame, text="App ID:", padx=10).grid(row=0, column=0, sticky="w")
        self.app_id_entry = ctk.CTkEntry(app_info_frame)
        self.app_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.app_id_entry.insert(0, self.cached_data.get("inputs", {}).get("app_id", ""))
        general_info_frame = ctk.CTkFrame(root, corner_radius=10)
        general_info_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        general_info_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(general_info_frame, text="Details:", padx=10).grid(row=0, column=0, sticky="w")
        self.details_entry = ctk.CTkEntry(general_info_frame)
        self.details_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.details_entry.insert(0, self.cached_data.get("inputs", {}).get("details", ""))
        ctk.CTkLabel(general_info_frame, text="State:", padx=10).grid(row=1, column=0, sticky="w")
        self.state_entry = ctk.CTkEntry(general_info_frame)
        self.state_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.state_entry.insert(0, self.cached_data.get("inputs", {}).get("state", ""))
        party_frame = ctk.CTkFrame(root, corner_radius=10)
        party_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        party_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(party_frame, text="Party:", padx=10).grid(row=0, column=0, sticky="w")
        party_inputs_frame = ctk.CTkFrame(party_frame)
        party_inputs_frame.grid(row=0, column=1, sticky="ew")
        party_inputs_frame.grid_columnconfigure(0, weight=1)
        party_inputs_frame.grid_columnconfigure(1, weight=1)
        self.party_current = ctk.CTkEntry(party_inputs_frame, placeholder_text="Current")
        self.party_current.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.party_current.insert(0, self.cached_data.get("inputs", {}).get("party_current", ""))
        self.party_max = ctk.CTkEntry(party_inputs_frame, placeholder_text="Max")
        self.party_max.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.party_max.insert(0, self.cached_data.get("inputs", {}).get("party_max", ""))
        timestamp_frame = ctk.CTkFrame(root, corner_radius=10)
        timestamp_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        timestamp_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(timestamp_frame, text="Timestamp:", padx=10).grid(row=0, column=0, sticky="w")
        self.timestamp_type = ctk.StringVar(value=self.cached_data.get("inputs", {}).get("timestamp_type", "None"))
        
        def update_timestamp_label(*args):
            if self.timestamp_type.get() == "Stay At":
                timestamp_label.configure(text="Delay (Seconds):")
            else:
                timestamp_label.configure(text="Custom Timestamp:")

        timestamp_options = ["None", "Local Time", "Custom Timestamp", "Since Program Started", "Since Connected", "Stay At"]
        timestamp_option_menu = ctk.CTkOptionMenu(timestamp_frame, variable=self.timestamp_type, values=timestamp_options)
        timestamp_option_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.timestamp_type.trace("w", update_timestamp_label)
        timestamp_label = ctk.CTkLabel(timestamp_frame, text="Custom Timestamp:", padx=10)
        timestamp_label.grid(row=1, column=0, sticky="w")

        self.custom_timestamp = ctk.CTkEntry(timestamp_frame)
        self.custom_timestamp.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.custom_timestamp.insert(0, self.cached_data.get("inputs", {}).get("custom_timestamp", ""))
        self.timestamp_type.trace("w", lambda *args: self.save_timestamp_options())
        images_frame = ctk.CTkFrame(root, corner_radius=10)
        images_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        images_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(images_frame, text="Large Image Key:", padx=10).grid(row=0, column=0, sticky="w")
        large_image_frame = ctk.CTkFrame(images_frame)
        large_image_frame.grid(row=0, column=1, sticky="ew")
        large_image_frame.grid_columnconfigure(0, weight=1)
        large_image_frame.grid_columnconfigure(1, weight=1)
        self.large_image_key = ctk.CTkEntry(large_image_frame, placeholder_text="Key")
        self.large_image_key.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.large_image_key.insert(0, self.cached_data.get("inputs", {}).get("large_image_key", ""))
        self.large_image_text = ctk.CTkEntry(large_image_frame, placeholder_text="Text")
        self.large_image_text.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.large_image_text.insert(0, self.cached_data.get("inputs", {}).get("large_image_text", ""))

        ctk.CTkLabel(images_frame, text="Small Image Key:", padx=10).grid(row=1, column=0, sticky="w")
        small_image_frame = ctk.CTkFrame(images_frame)
        small_image_frame.grid(row=1, column=1, sticky="ew")
        small_image_frame.grid_columnconfigure(0, weight=1)
        small_image_frame.grid_columnconfigure(1, weight=1)
        self.small_image_key = ctk.CTkEntry(small_image_frame, placeholder_text="Key")
        self.small_image_key.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.small_image_key.insert(0, self.cached_data.get("inputs", {}).get("small_image_key", ""))
        self.small_image_text = ctk.CTkEntry(small_image_frame, placeholder_text="Text")
        self.small_image_text.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.small_image_text.insert(0, self.cached_data.get("inputs", {}).get("small_image_text", ""))
        buttons_frame = ctk.CTkFrame(root, corner_radius=10)
        buttons_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        buttons_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(buttons_frame, text="Button 1:", padx=10).grid(row=0, column=0, sticky="w")
        button1_frame = ctk.CTkFrame(buttons_frame)
        button1_frame.grid(row=0, column=1, sticky="ew")
        button1_frame.grid_columnconfigure(0, weight=1)
        button1_frame.grid_columnconfigure(1, weight=1)
        self.button1_text = ctk.CTkEntry(button1_frame, placeholder_text="Text")
        self.button1_text.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.button1_text.insert(0, self.cached_data.get("inputs", {}).get("button1_text", ""))
        self.button1_url = ctk.CTkEntry(button1_frame, placeholder_text="URL")
        self.button1_url.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.button1_url.insert(0, self.cached_data.get("inputs", {}).get("button1_url", ""))

        ctk.CTkLabel(buttons_frame, text="Button 2:", padx=10).grid(row=1, column=0, sticky="w")
        button2_frame = ctk.CTkFrame(buttons_frame)
        button2_frame.grid(row=1, column=1, sticky="ew")
        button2_frame.grid_columnconfigure(0, weight=1)
        button2_frame.grid_columnconfigure(1, weight=1)
        self.button2_text = ctk.CTkEntry(button2_frame, placeholder_text="Text")
        self.button2_text.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.button2_text.insert(0, self.cached_data.get("inputs", {}).get("button2_text", ""))
        self.button2_url = ctk.CTkEntry(button2_frame, placeholder_text="URL")
        self.button2_url.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.button2_url.insert(0, self.cached_data.get("inputs", {}).get("button2_url", ""))
        
        def rgb(value):
            return f"
        normal = rgb((255, 255, 255))
        keywords = rgb((70, 130, 180))
        comments = rgb((100, 149, 237))
        string = rgb((135, 206, 250))
        background = rgb((38, 38, 38))
        font = ('Consolas', 15)
        repl = [
            ['(^| )(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)($| )', keywords],
            ['".*?"', string],
            ['\'.*?\'', string],
            ['
        ]
            
        previousText = ''
        self.script_frame = ctk.CTkFrame(root, corner_radius=10)
        self.script_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.script_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.script_frame, text="Custom Script:", padx=10).pack(side="top", anchor="w")
        self.script_area = ctk.CTkTextbox(self.script_frame, height=200, wrap="word", font=font, fg_color=background, text_color=normal)
        self.script_area.pack(fill="both", expand=True, padx=10, pady=5)
        
        def changes(event=None):
            previousText = ""
            if self.script_area.get("1.0", "end") == previousText:
                return
            try:
                start_idx = self.script_area.index("sel.first")
                end_idx = self.script_area.index("sel.last")
                selected_text = self.script_area.get(start_idx, end_idx)
            except:
                selected_text = ""
            for tag in self.script_area.tag_names():
                self.script_area.tag_remove(tag, "1.0", "end")

            i = 0
            for pattern, color in repl:
                for start, end in search_re(pattern, self.script_area.get("1.0", "end")):
                    self.script_area.tag_add(f'{i}', start, end)
                    self.script_area.tag_config(f'{i}', foreground=color)
                    i += 1
            self.script_area.tag_config("sel", foreground="white", background="
            if selected_text:
                self.script_area.tag_add("sel", start_idx, end_idx)
            previousText = self.script_area.get("1.0", "end")
            
        def search_re(pattern, text):
            matches = []
            text = text.splitlines()
            for i, line in enumerate(text):
                for match in re.finditer(pattern, line):
                    matches.append((f"{i + 1}.{match.start()}", f"{i + 1}.{match.end()}"))
            return matches
        self.script_area.bind("<KeyRelease>", changes)

        saved_script = self.cached_data.get("script", "")
        self.script_area.insert("1.0", saved_script)
        changes()
        background_icon_image = load_png_image_from_file(file_background)
        background_icon = ctk.CTkImage(light_image=background_icon_image,
                        dark_image=background_icon_image, 
                        size=(20, 15))
        self.background_mode_var = ctk.StringVar(value="off")
        self.background_button = ctk.CTkButton(
            root, 
            image=background_icon, 
            text="",
            command=self.toggle_background,
            width=25,
            height=20,
        )

        self.background_button.grid(row=7, column=0, padx=15, pady=10, sticky="w")
        self.switch_var = ctk.StringVar(value="off")
        self.switch_button = ctk.CTkSwitch(root, text="Disconnect / Connect", variable=self.switch_var, command=self.toggle_rpc, onvalue="on", offvalue="off")
        self.switch_button.grid(row=7, column=0, columnspan=2, pady=10, sticky="s")

        self.program_start_time = time.time()
        self.connected_time = None
        self.output_capture = OutputCapture()
        self.script_thread = None
        self.update_presence_thread = None
        self.rpc = None
        self.running = True
        self.fade_step = 0.05
        self.fade_duration = 500
        self.fade_in_step_count = int(self.fade_duration / self.fade_step)

        self.fade_in()
        self.is_window_hidden = False
        self.icon = None

        self.icon_thread = threading.Thread(target=self.create_tray_icon)
        self.icon_thread.start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def toggle_rpc(self):
        if self.switch_var.get() == "on":
            self.start_rpc()
        else:
            self.stop_rpc()

    def fade_in(self, current_step=0):
        fade_duration = 500
        fade_steps = 100
        fade_step_delay = fade_duration / fade_steps
        
        if current_step <= fade_steps:
            eased_value = self.ease_out_cubic(current_step / fade_steps)
            self.root.attributes("-alpha", eased_value)
            self.root.after(int(fade_step_delay), self.fade_in, current_step + 1)
        else:
            self.root.attributes("-alpha", 1)

    def ease_out_cubic(self, x):
        return 1 - (1 - x) ** 3
    
    def create_tray_icon(self):
        icon_image = self.create_image(file_background)
  
        def connect_action(icon, item):
            self.switch_var.set("on")
            self.toggle_rpc()

        def disconnect_action(icon, item):
            self.switch_var.set("off")
            self.toggle_rpc()
        menu = (
            item('Show Window', self.show_window, default=True, visible=True),
            item('Connect', connect_action),
            item('Disconnect', disconnect_action),
            item('Exit', self.on_close)
        )
        self.icon = pystray.Icon("RichPresence", icon_image, menu=menu)
        self.icon.run()

    def create_image(self, file_path):
        image = load_png_image_from_file(file_path)
        image = image.resize((64, 64))

        return image


    def toggle_background(self):
        if self.is_window_hidden:
            self.root.deiconify()
            self.icon.visible = True
            self.is_window_hidden = False
        else:
            self.root.withdraw()
            self.icon.visible = True
            self.is_window_hidden = True

    def show_window(self, icon, item):
        self.root.deiconify()
        self.is_window_hidden = False
        self.icon.visible = True
        self.fade_in()

    def update_presence(self):
        while self.running:
            try:
                if not self.running:
                    break
                details = self.replace_script_tags(self.details_entry.get())
                state = self.replace_script_tags(self.state_entry.get())
                if not details or not state:
                    messagebox.showwarning("Input Error", "Details and state cannot be empty!")
                    self.running = False
                    break
                timestamp_type = self.timestamp_type.get()
                timestamp = None
                if timestamp_type == "Local Time":
                    timestamp = int(time.time())
                elif timestamp_type == "Custom Timestamp":
                    try:
                        timestamp = int(datetime.strptime(self.custom_timestamp.get(), "%Y-%m-%d %H:%M:%S").timestamp())
                    except ValueError:
                        messagebox.showerror("Error", "Invalid custom timestamp format! Use YYYY-MM-DD HH:MM:SS.")
                        self.running = False
                        break
                elif timestamp_type == "Since Program Started":
                    if not self.program_start_time:
                        messagebox.showerror("Error", "Program start time is unavailable.")
                        self.running = False
                        break
                    timestamp = int(self.program_start_time)
                elif timestamp_type == "Since Connected":
                    if self.connected_time is None:
                        timestamp = None
                    else:
                        timestamp = int(self.connected_time)
                elif timestamp_type == "Stay At":
                    if self.connected_time is None:
                        timestamp = None
                    else:
                        try:
                            user_input = self.custom_timestamp.get().strip()
                            if not user_input.isdigit():
                                raise ValueError("Custom timestamp delay must be a valid integer.")
                            delay_seconds = int(user_input)

                            current_time_unix = int(time.time())
                            timestamp = current_time_unix - delay_seconds
                        except ValueError as ve:
                            messagebox.showerror("Error", f"Invalid input! Please enter a valid number for delay in seconds.\nError: {ve}")
                            self.running = False
                            break
                        except Exception as e:
                            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
                            self.running = False
                            break
                try:
                    party_current = int(self.party_current.get()) if self.party_current.get() else None
                    party_max = int(self.party_max.get()) if self.party_max.get() else None
                except ValueError:
                    messagebox.showerror("Error", "Party size must be a valid number.")
                    self.running = False
                    break

                party_size = (party_current, party_max) if party_current is not None and party_max is not None else None
                large_image_key = self.large_image_key.get().strip() or None
                large_image_text = self.large_image_text.get().strip() or None
                small_image_key = self.small_image_key.get().strip() or None
                small_image_text = self.small_image_text.get().strip() or None

                buttons = []
                if self.button1_text.get() and self.button1_url.get():
                    buttons.append({"label": self.button1_text.get(), "url": self.button1_url.get()})
                if self.button2_text.get() and self.button2_url.get():
                    buttons.append({"label": self.button2_text.get(), "url": self.button2_url.get()})
                payload = {
                    "details": details,
                    "state": state,
                    "party_size": party_size,
                    "large_image": large_image_key,
                    "large_text": large_image_text,
                    "small_image": small_image_key,
                    "small_text": small_image_text,
                    "start": timestamp,
                    "buttons": buttons if buttons else None,
                }
                payload = {k: v for k, v in payload.items() if v is not None}
                if self.rpc:
                    try:
                        self.rpc.update(**payload)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to update presence: {e}")
                        self.running = False
                        break
                if timestamp_type == "Stay At":
                    time.sleep(1)
                else:
                    time.sleep(1)

            except Exception as e:
                self.running = False
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
                break

    def start_rpc(self):
        app_id = self.app_id_entry.get().strip()
        if not app_id:
            messagebox.showerror("Error", "App ID is required!")
            self.switch_var.set("off")
            return

        try:
            self.rpc = Presence(app_id, loop=asyncio.new_event_loop())
            self.rpc.connect()
            self.running = True
            self.connected_time = time.time()
            self.start_script_thread()
            self.update_presence_thread = threading.Thread(target=self.update_presence, daemon=True)
            self.update_presence_thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
            self.switch_var.set("off")

    def stop_rpc(self):
        self.running = False
        if self.rpc:
            try:
                self.rpc.close()
            except Exception as e:
                print(f"Error while stopping RPC: {e}")
        self.rpc = None
        self.output_capture = OutputCapture()
        if self.script_thread and self.script_thread.is_alive():
            thread_id = self.script_thread.ident
            try:
                result = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
                if result > 0:
                    print("Thread forcefully terminated.")
                else:
                    print("Failed to terminate the thread.")
            except Exception as e:
                print(f"Error while terminating the thread: {e}")
        if self.update_presence_thread and self.update_presence_thread.is_alive():
            thread_id = self.update_presence_thread.ident
            try:
                result = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
                if result > 0:
                    print("Update presence thread forcefully terminated.")
                else:
                    print("Failed to terminate the update presence thread.")
            except Exception as e:
                print(f"Error while terminating the update presence thread: {e}")

        messagebox.showinfo("Disconnected", "Rich Presence stopped!")

    def start_script_thread(self):
        self.script_thread = threading.Thread(target=self.run_user_script, daemon=True)
        self.script_thread.start()

    def run_user_script(self):
        try:
            script_globals = {
                "CustomLibrary": CustomLibrary,
                "time": time,
                "print": self.output_capture.write,
                "__builtins__": __builtins__,
            }
            exec(self.script_area.get("1.0", tk.END), script_globals)
        except Exception as e:
            self.output_capture.write(f"Script Error: {e}\n")
            messagebox.showerror("Script Error", f"An error occurred in your script: {e}")

    def replace_script_tags(self, text):
        while "<@script>" in text:
            latest_output = self.output_capture.read_latest_line()
            if latest_output:
                text = text.replace("<@script>", latest_output, 1)
                self.output_capture.clear()
        return text

    def save_inputs(self):
        data = {
            "app_id": self.app_id_entry.get(),
            "details": self.details_entry.get(),
            "state": self.state_entry.get(),
            "party_current": self.party_current.get(),
            "party_max": self.party_max.get(),
            "large_image_key": self.large_image_key.get(),
            "large_image_text": self.large_image_text.get(),
            "small_image_key": self.small_image_key.get(),
            "small_image_text": self.small_image_text.get(),
            "custom_timestamp": self.custom_timestamp.get(),
            "timestamp_type": self.timestamp_type.get(),
            "button1_text": self.button1_text.get(),
            "button1_url": self.button1_url.get(),
            "button2_text": self.button2_text.get(),
            "button2_url": self.button2_url.get(),
        }
        script_content = self.script_area.get("1.0", tk.END)
        save_cache(data, script_content)

    def save_timestamp_options(self):
        timestamp_data = {
            "timestamp_type": self.timestamp_type.get(),
            "custom_timestamp": self.custom_timestamp.get()
        }
        save_cache(timestamp_data)

    def on_close(self):
        self.save_inputs()
        self.stop_rpc()
        self.icon.stop()
        self.root.quit()
        if self.script_thread and self.script_thread.is_alive():
            self.running = False
            self.script_thread.join(timeout=5)
        self.root.quit()

if __name__ == "__main__":
    root = ctk.CTk()
    app = CustomRichPresenceApp(root)
    root.mainloop()
