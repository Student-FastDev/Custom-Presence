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

# Use tempfile to store the cache file.
CACHE_FILE = "cache.json"
file_background = "background_task.png"

def save_cache(data, script_content=None):
    """
    Clear the existing cache and save the new input data to a JSON file.

    Args:
        data (dict): A dictionary containing the input data.
        script_content (str, optional): The content of the script to be saved. Defaults to None.

    Returns:
        None.
    """
    try:
        # Clear the existing cache by deleting the file if it exists.
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)

        # Create a dictionary to store both input data and script content.
        cache_data = {"inputs": data}
        if script_content:
            cache_data["script"] = script_content

        # Save the new data to the cache file.
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=4)
        print(f"Cache cleared and saved to: {CACHE_FILE}")

    except Exception as e:
        print(f"Error saving cache: {e}")

def load_cache():
    """
    Load the input data and script content from the cached JSON file if it exists.

    Args:
        None.

    Returns:
        dict: A dictionary containing the cached data, or an empty dictionary if no cache is found.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
                inputs = cache_data.get("inputs", {})
                script_content = cache_data.get("script", "")
                return {"inputs": inputs, "script": script_content}
        except Exception as e:
            print(f"Error loading cache: {e}")
    return {"inputs": {}, "script": ""}  # Return an empty dictionary if no cache is found.

def load_png_image_from_file(file_path):
    """
    Load a PNG image from a file, resize it to 40x40 pixels, and change its color to white
    while preserving the alpha channel (transparency).

    Args:
        file_path (str): The path to the PNG file to be loaded.

    Returns:
        Image: A PIL Image object representing the resized and color-transformed PNG file.
    """
    # Open the PNG image with PIL
    image = Image.open(file_path)

    # Resize the image to 40x40 pixels (or adjust the size as needed)
    image = image.resize((20, 15))

    # Convert the image to RGBA (to ensure we have an alpha channel)
    image = image.convert("RGBA")
    pixels = image.load()

    # Make the image white by setting RGB to 255, while keeping the alpha value intact
    for i in range(image.width):
        for j in range(image.height):
            r, g, b, a = pixels[i, j]  # Extract RGB and alpha values
            if a > 0:  # Only modify pixels that are not fully transparent
                pixels[i, j] = (255, 255, 255, a)  # Set RGB to white, preserve alpha

    return image

class OutputCapture(io.StringIO):
    """
    A class to capture printed output from a user script and display it in the console.
    It extends `io.StringIO` and provides thread-safe methods for capturing, reading,
    and clearing the output.
    """
    def __init__(self):
        """Initialize the OutputCapture object with a threading lock."""
        super().__init__()
        self.lock = threading.Lock()

    def write(self, *args):
        """
        Capture printed output while ensuring thread safety.
        
        Args:
            list: One or more arguments to write as output.

        Returns:
            None.
        """
        with self.lock:
            # Join all arguments into a single string, separating by a space.
            output = ' '.join(map(str, args))
            super().write(output + '\n')  # Ensure it matches print's default behavior (newline at the end).
            # Print the output to the console as well.
            sys.stdout.write(output + '\n')

    def read_latest_line(self):
        """
        Retrieve the most recent line of captured output.
        
        Args:
            None

        Returns:
            str: The latest line of output, or an empty string if no output is captured.
        """
        with self.lock:
            lines = self.getvalue().strip().split("\n")
            return lines[-1] if lines else ""

    def clear(self):
        """
        Clear all captured output from the internal buffer.
        """
        with self.lock:
            self.seek(0)
            self.truncate(0)


class CustomLibrary:
    """
    A utility library providing static methods for common tasks, such as getting the current time,
    generating sequential levels, and generating random numbers within a range.
    """
    @staticmethod
    def get_time():
        """
        Get the current date and time as a formatted string.
        
        Args:
            None
        Returns:
            str: Current date and time in the format "YYYY-MM-DD HH:MM:SS".
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def generate_levels(count):
        """
        Generate a list of sequential level names.
        
        Args:
            count (int): The number of levels to generate.
        
        Returns:
            list: A list of strings representing levels (e.g., ["Level 1", "Level 2", ...]).
        """
        return [f"Level {i+1}" for i in range(count)]

    @staticmethod
    def generate_number(start, end):
        """
        Generate a random integer within a specified range.
        
        Args:
            start (int): The start of the range (inclusive).
            end (int): The end of the range (inclusive).
        
        Returns:
            int: A randomly generated integer between `start` and `end`.
        """
        import random
        return random.randint(start, end)


class CustomRichPresenceApp:
    def __init__(self, root):
        """
        Initialize the CustomRichPresenceApp class to create a GUI application for managing Discord Rich Presence.
        
        Args:
            root (tk.Tk): The root Tkinter window.

        Returns:
            None.
        """
        self.root = root
        self.root.title("Custom Discord Rich Presence")
        self.rpc = None
        self.running = False
        self.script_thread = None
        self.output_capture = OutputCapture()

        # Load the cached data on startup
        self.cached_data = load_cache()

        # Configure root to be responsive.
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(6, weight=1)  # Make the self.script_frame expand with the window.

        # Set initial opacity (0 means fully transparent, 1 means fully opaque)
        self.root.attributes("-alpha", 0)  # Start with the window invisible

        # Frame: App Info.
        app_info_frame = ctk.CTkFrame(root, corner_radius=10)
        app_info_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        app_info_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(app_info_frame, text="App ID:", padx=10).grid(row=0, column=0, sticky="w")
        self.app_id_entry = ctk.CTkEntry(app_info_frame)
        self.app_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.app_id_entry.insert(0, self.cached_data.get("inputs", {}).get("app_id", ""))

        # Frame: General Info.
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

        # Frame: Party Info.
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

        # Frame: Timestamp
        timestamp_frame = ctk.CTkFrame(root, corner_radius=10)
        timestamp_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        timestamp_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(timestamp_frame, text="Timestamp:", padx=10).grid(row=0, column=0, sticky="w")
        self.timestamp_type = ctk.StringVar(value=self.cached_data.get("inputs", {}).get("timestamp_type", "None"))

        # Function to update label based on selected timestamp option.
        def update_timestamp_label(*args):
            if self.timestamp_type.get() == "Stay At":
                timestamp_label.configure(text="Delay (Seconds):")
            else:
                timestamp_label.configure(text="Custom Timestamp:")

        timestamp_options = ["None", "Local Time", "Custom Timestamp", "Since Program Started", "Since Connected", "Stay At"]
        timestamp_option_menu = ctk.CTkOptionMenu(timestamp_frame, variable=self.timestamp_type, values=timestamp_options)
        timestamp_option_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Add event binding to detect option change.
        self.timestamp_type.trace("w", update_timestamp_label)

        # Create the label for the custom timestamp field.
        timestamp_label = ctk.CTkLabel(timestamp_frame, text="Custom Timestamp:", padx=10)
        timestamp_label.grid(row=1, column=0, sticky="w")

        self.custom_timestamp = ctk.CTkEntry(timestamp_frame)
        self.custom_timestamp.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.custom_timestamp.insert(0, self.cached_data.get("inputs", {}).get("custom_timestamp", ""))  # Load custom timestamp from cache

        # Save timestamp option when the user selects it
        self.timestamp_type.trace("w", lambda *args: self.save_timestamp_options())

        # Frame: Images
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
        self.large_image_key.insert(0, self.cached_data.get("inputs", {}).get("large_image_key", ""))  # Load large image key from cache
        self.large_image_text = ctk.CTkEntry(large_image_frame, placeholder_text="Text")
        self.large_image_text.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.large_image_text.insert(0, self.cached_data.get("inputs", {}).get("large_image_text", ""))  # Load large image text from cache

        ctk.CTkLabel(images_frame, text="Small Image Key:", padx=10).grid(row=1, column=0, sticky="w")
        small_image_frame = ctk.CTkFrame(images_frame)
        small_image_frame.grid(row=1, column=1, sticky="ew")
        small_image_frame.grid_columnconfigure(0, weight=1)
        small_image_frame.grid_columnconfigure(1, weight=1)
        self.small_image_key = ctk.CTkEntry(small_image_frame, placeholder_text="Key")
        self.small_image_key.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.small_image_key.insert(0, self.cached_data.get("inputs", {}).get("small_image_key", ""))  # Load small image key from cache
        self.small_image_text = ctk.CTkEntry(small_image_frame, placeholder_text="Text")
        self.small_image_text.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.small_image_text.insert(0, self.cached_data.get("inputs", {}).get("small_image_text", ""))  # Load small image text from cache

        # Frame: Buttons
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
        self.button1_text.insert(0, self.cached_data.get("inputs", {}).get("button1_text", ""))  # Load button 1 text from cache
        self.button1_url = ctk.CTkEntry(button1_frame, placeholder_text="URL")
        self.button1_url.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.button1_url.insert(0, self.cached_data.get("inputs", {}).get("button1_url", ""))  # Load button 1 URL from cache

        ctk.CTkLabel(buttons_frame, text="Button 2:", padx=10).grid(row=1, column=0, sticky="w")
        button2_frame = ctk.CTkFrame(buttons_frame)
        button2_frame.grid(row=1, column=1, sticky="ew")
        button2_frame.grid_columnconfigure(0, weight=1)
        button2_frame.grid_columnconfigure(1, weight=1)
        self.button2_text = ctk.CTkEntry(button2_frame, placeholder_text="Text")
        self.button2_text.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.button2_text.insert(0, self.cached_data.get("inputs", {}).get("button2_text", ""))  # Load button 2 text from cache
        self.button2_url = ctk.CTkEntry(button2_frame, placeholder_text="URL")
        self.button2_url.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.button2_url.insert(0, self.cached_data.get("inputs", {}).get("button2_url", ""))  # Load button 2 URL from cache

       # Define RGB function.
        def rgb(value):
            return f"#{value[0]:02x}{value[1]:02x}{value[2]:02x}"

        # Define colors for different tokens (shades of blue).
        normal = rgb((255, 255, 255))  # light blue for default text color.
        keywords = rgb((70, 130, 180))  # steel blue for keywords.
        comments = rgb((100, 149, 237))  # cornflower blue for comments.
        string = rgb((135, 206, 250))  # light sky blue for strings.
        background = rgb((38, 38, 38))  # background color (dark theme).

        # Define the font as a tuple.
        font = ('Consolas', 15)

        # Define list of regex patterns for each token.
        repl = [
            ['(^| )(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)($| )', keywords],  # keywords.
            ['".*?"', string],  # strings inside double quotes.
            ['\'.*?\'', string],  # strings inside single quotes.
            ['#.*?$', comments],  # comments starting with #.
        ]

        # Initialize the previousText variable globally.
        previousText = ''

        # Frame: Custom Script.
        self.script_frame = ctk.CTkFrame(root, corner_radius=10)
        self.script_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.script_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.script_frame, text="Custom Script:", padx=10).pack(side="top", anchor="w")

        # Textbox for the script area with dark background and light text.
        self.script_area = ctk.CTkTextbox(self.script_frame, height=200, wrap="word", font=font, fg_color=background, text_color=normal)
        self.script_area.pack(fill="both", expand=True, padx=10, pady=5)

       # Function to highlight syntax.
        def changes(event=None):
            """
            Function to highlight syntax in a text area by applying colors to text patterns.

            Args:
                event (tk.Event, optional): An optional Tkinter event. This parameter is provided for handling event-driven updates.

            Returns:
                None.
            """
            previousText = ""  # Ensure to use the global previousText.
            if self.script_area.get("1.0", "end") == previousText:
                return

            # Check if any text is selected.
            try:
                start_idx = self.script_area.index("sel.first")
                end_idx = self.script_area.index("sel.last")
                selected_text = self.script_area.get(start_idx, end_idx)  # Save the selected text.
            except:
                # No selection, proceed with syntax highlighting.
                selected_text = ""

            # Remove all existing tags.
            for tag in self.script_area.tag_names():
                self.script_area.tag_remove(tag, "1.0", "end")

            i = 0
            for pattern, color in repl:
                for start, end in search_re(pattern, self.script_area.get("1.0", "end")):
                    self.script_area.tag_add(f'{i}', start, end)
                    self.script_area.tag_config(f'{i}', foreground=color)
                    i += 1

            # Change the selection style.
            self.script_area.tag_config("sel", foreground="white", background="#4682B4")  # Modify these colors as needed.

            # Restore the selection if there was any.
            if selected_text:
                self.script_area.tag_add("sel", start_idx, end_idx)

            # Update previousText.
            previousText = self.script_area.get("1.0", "end")

        # Function to search regex pattern in the text.
        def search_re(pattern, text):
            """
            Search for a regex pattern in the given text and return the matches with their line and column positions.
            
            Args:
                pattern (str): The regular expression pattern to search for.
                text (str): The text in which to search for the pattern. This is expected to be a multiline string.
            
            Returns:
                list: A list of tuples where each tuple contains the start and end positions of a match in the format 
                    ("line.column_start", "line.column_end").
            """
            matches = []
            text = text.splitlines()
            for i, line in enumerate(text):
                for match in re.finditer(pattern, line):
                    matches.append((f"{i + 1}.{match.start()}", f"{i + 1}.{match.end()}"))
            return matches

        # Bind events.
        self.script_area.bind("<KeyRelease>", changes)

        saved_script = self.cached_data.get("script", "")
        self.script_area.insert("1.0", saved_script)

        # Initial syntax highlighting.
        changes()

        # Background Toggle Button (Placed to the Left)
        background_icon_image = load_png_image_from_file(file_background)
        background_icon = ctk.CTkImage(light_image=background_icon_image,
                        dark_image=background_icon_image, 
                        size=(20, 15))  # Adjust the size as per your needs

        # Create a button with the image and no text, and ensure it fits the image size
        self.background_mode_var = ctk.StringVar(value="off")
        self.background_button = ctk.CTkButton(
            root, 
            image=background_icon, 
            text="",  # No text
            command=self.toggle_background,
            width=25,  # Set the width to fit the icon
            height=20,  # Set the height to fit the icon
        )

        self.background_button.grid(row=7, column=0, padx=15, pady=10, sticky="w")

        # Connect/Disconnect Switch.
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
        self.fade_step = 0.05  # The increment step for opacity change
        self.fade_duration = 500  # Time duration for full fade-in in milliseconds
        self.fade_in_step_count = int(self.fade_duration / self.fade_step)

        self.fade_in()

        # Initially, the app window is visible
        self.is_window_hidden = False  # Define this variable here to track window visibility
        self.icon = None

        self.icon_thread = threading.Thread(target=self.create_tray_icon)
        self.icon_thread.start()

        # Ensure proper cleanup on exit.
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def toggle_rpc(self):
        """
        Toggle the Rich Presence connection state.

        Args:
            None.

        Returns:
            None.
        """
        if self.switch_var.get() == "on":
            self.start_rpc()
        else:
            self.stop_rpc()

    def fade_in(self, current_step=0):
        """
        Fade-in the window by gradually increasing the opacity with easing.
        
        Args:
            current_step (int): The current step in the fade-in animation.

        Returns:
            None.
        """
        # Define the fade parameters
        fade_duration = 500  # Total time for fade-in (in ms)
        fade_steps = 100  # Number of steps to complete the fade-in
        fade_step_delay = fade_duration / fade_steps  # Delay between each step
        
        if current_step <= fade_steps:
            # Apply easeOutSine easing function to the opacity calculation
            eased_value = self.ease_out_cubic(current_step / fade_steps)
            
            # Set the window opacity (value will be between 0 and 1 based on eased_value)
            self.root.attributes("-alpha", eased_value)
            
            # Schedule the next step
            self.root.after(int(fade_step_delay), self.fade_in, current_step + 1)
        else:
            # Once fade-in is complete, ensure opacity is fully 1 (fully visible)
            self.root.attributes("-alpha", 1)

    def ease_out_cubic(self, x):
        """
        Ease out cubic function for smoother fade-in.
        
        Args:
            x (float): The normalized progress value (between 0 and 1).
        
        Returns:
            float: The eased value for smooth animation.
        """
        return 1 - (1 - x) ** 3
    
    def create_tray_icon(self):
        """
        Creates and manages the system tray icon for the application.
        It includes options for showing the window, connecting, disconnecting, and exiting the application.

        Args:
            None directly for this method, as it's part of a class and references instance variables and methods.

        Returns:
            None. This method creates and manages the system tray icon and its menu, running in the background.
        """
        # Create an icon for the tray
        icon_image = self.create_image(file_background)
  
        def connect_action(icon, item):
            # Set the switch to "on" (Connect)
            self.switch_var.set("on")
            self.toggle_rpc()  # Trigger the action as if the user toggled the switch

        def disconnect_action(icon, item):
            # Set the switch to "off" (Disconnect)
            self.switch_var.set("off")
            self.toggle_rpc()  # Trigger the action as if the user toggled the switch

        # Create a menu with options, including the new ones
        menu = (
            item('Show Window', self.show_window, default=True, visible=True),
            item('Connect', connect_action),
            item('Disconnect', disconnect_action),
            item('Exit', self.on_close)
        )

        # Create the system tray icon and run in the background
        self.icon = pystray.Icon("RichPresence", icon_image, menu=menu)
        
        # Make the tray icon clickable to show window
        self.icon.run()

    def create_image(self, file_path):
        """
        Load a PNG image from a file, resize it to 64x64 pixels, and return it.

        Args:
            file_path (str): The path to the PNG file to be loaded.

        Returns:
            Image: A PIL Image object representing the resized PNG file.
        """
        # Load and resize the image using load_png_image_from_file
        image = load_png_image_from_file(file_path)

        # Resize it to 64x64 to ensure it's the right size for the tray icon
        image = image.resize((64, 64))

        return image


    def toggle_background(self):
        """
        Toggle the visibility of the main window and keep the tray icon visible.
        
        If the window is hidden, it is shown; if it's visible, it is hidden. 
        The tray icon remains visible either way.
        
        Args:
            None.
        
        Returns:
            None.
        """
        if self.is_window_hidden:
            # Show the window if it's hidden
            self.root.deiconify()  # Show the Tkinter window
            self.icon.visible = True  # Ensure the tray icon is visible
            self.is_window_hidden = False
        else:
            # Hide the window to run in the background
            self.root.withdraw()  # Hide the Tkinter window
            self.icon.visible = True  # Tray icon remains visible
            self.is_window_hidden = True

    def show_window(self, icon, item):
        """
        Show the window when the tray icon menu item is clicked.
        
        Ensures that the window is restored from the taskbar and applies a fade-in effect.
        
        Args:
            icon (pystray.Icon): The system tray icon object that was clicked.
            item (pystray.MenuItem): The tray menu item that was clicked.
        
        Returns:
            None.
        """
        # Show the window again if the tray icon menu item is clicked
        self.root.deiconify()
        self.is_window_hidden = False
        self.icon.visible = True  # Ensure tray icon is still visible
        self.fade_in()

    def update_presence(self):
        """
        Continuously update the Discord Rich Presence with the provided details.

        Args:
            None.

        Returns:
            None.
        """
        while self.running:
            try:
                # Ensure we stop the thread gracefully if needed.
                if not self.running:
                    break

                # Retrieve user inputs and validate them.
                details = self.replace_script_tags(self.details_entry.get())
                state = self.replace_script_tags(self.state_entry.get())

                # Validate details and state are non-empty strings.
                if not details or not state:
                    messagebox.showwarning("Input Error", "Details and state cannot be empty!")
                    self.running = False
                    break

                # Parse timestamps.
                timestamp_type = self.timestamp_type.get()
                timestamp = None

                # Validate timestamp formats.
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
                        timestamp = None  # If not connected yet, return None.
                    else:
                        timestamp = int(self.connected_time)  # Use the exact time of connection.
                elif timestamp_type == "Stay At":
                    if self.connected_time is None:
                        timestamp = None  # If not connected yet, return None.
                    else:
                        try:
                            # Get the custom timestamp (delay in seconds) entered by the user.
                            user_input = self.custom_timestamp.get().strip()
                            if not user_input.isdigit():
                                raise ValueError("Custom timestamp delay must be a valid integer.")
                            delay_seconds = int(user_input)  # Ensure the user input is an integer (seconds).

                            current_time_unix = int(time.time())  # Current time in Unix format
                            timestamp = current_time_unix - delay_seconds  # Subtract the delay from current time.
                        except ValueError as ve:
                            messagebox.showerror("Error", f"Invalid input! Please enter a valid number for delay in seconds.\nError: {ve}")
                            self.running = False
                            break
                        except Exception as e:
                            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
                            self.running = False
                            break

                # Validate party size.
                try:
                    party_current = int(self.party_current.get()) if self.party_current.get() else None
                    party_max = int(self.party_max.get()) if self.party_max.get() else None
                except ValueError:
                    messagebox.showerror("Error", "Party size must be a valid number.")
                    self.running = False
                    break

                party_size = (party_current, party_max) if party_current is not None and party_max is not None else None

                # Validate image keys and buttons.
                large_image_key = self.large_image_key.get().strip() or None
                large_image_text = self.large_image_text.get().strip() or None
                small_image_key = self.small_image_key.get().strip() or None
                small_image_text = self.small_image_text.get().strip() or None

                buttons = []
                if self.button1_text.get() and self.button1_url.get():
                    buttons.append({"label": self.button1_text.get(), "url": self.button1_url.get()})
                if self.button2_text.get() and self.button2_url.get():
                    buttons.append({"label": self.button2_text.get(), "url": self.button2_url.get()})

                # Prepare the payload.
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

                # Ensure payload does not contain None values.
                payload = {k: v for k, v in payload.items() if v is not None}

                # Update the presence (check if rpc exists).
                if self.rpc:
                    try:
                        self.rpc.update(**payload)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to update presence: {e}")
                        self.running = False
                        break

                # If the timestamp is set to "Stay At", continuously update every second.
                if timestamp_type == "Stay At":
                    time.sleep(1)
                else:
                    time.sleep(1)  # Check output every second.

            except Exception as e:
                self.running = False
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
                break

    def start_rpc(self):
        """
        This function initializes the RPC connection, connects to the Discord
        Rich Presence API using the provided App ID, and starts the relevant
        threads to update the presence.

        Args:
            None.

        Returns:
            None.
        """
        app_id = self.app_id_entry.get().strip()
        if not app_id:
            messagebox.showerror("Error", "App ID is required!")
            self.switch_var.set("off")  # Reset the switch if starting fails.
            return

        try:
            self.rpc = Presence(app_id, loop=asyncio.new_event_loop())  # Use a separate event loop.
            self.rpc.connect()
            self.running = True
            self.connected_time = time.time()  # Store the exact time of connection.
            self.start_script_thread()
            self.update_presence_thread = threading.Thread(target=self.update_presence, daemon=True)
            self.update_presence_thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
            self.switch_var.set("off")  # Reset the switch if connection fails.

    def stop_rpc(self):
        """
        Stop the Rich Presence (RPC) service and ensure all related resources are properly cleaned up.

        Args:
            None.

        Returns:
            None.
        """
        self.running = False
        if self.rpc:
            try:
                self.rpc.close()
            except Exception as e:
                print(f"Error while stopping RPC: {e}")
        self.rpc = None
        self.output_capture = OutputCapture()  # Reset the output capture to clear previous output.

        # Forcefully terminate the script thread if it's running.
        if self.script_thread and self.script_thread.is_alive():
            thread_id = self.script_thread.ident  # Get the thread ID.
            try:
                result = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
                if result > 0:
                    print("Thread forcefully terminated.")
                else:
                    print("Failed to terminate the thread.")
            except Exception as e:
                print(f"Error while terminating the thread: {e}")

        # Forcefully terminate the update_presence thread if it's running.
        if self.update_presence_thread and self.update_presence_thread.is_alive():
            thread_id = self.update_presence_thread.ident  # Get the thread ID.
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
        """
        Start the script execution in a separate thread.

        Args:
            None.

        Returns:
            None.
        """
        self.script_thread = threading.Thread(target=self.run_user_script, daemon=True)
        self.script_thread.start()

    def run_user_script(self):
        """
        Simulate a long-running user script.

        Args:
            None.

        Returns:
            None.
        """
        try:
            # Define the global context for the script.
            script_globals = {
                "CustomLibrary": CustomLibrary,
                "time": time,
                "print": self.output_capture.write,  # Redirect print to OutputCapture.
                "__builtins__": __builtins__,  # Ensure access to built-in functions like `print`.
            }

            # Execute the script from the custom text area.
            exec(self.script_area.get("1.0", tk.END), script_globals)
        except Exception as e:
            # Capture any errors that occur in the output.
            self.output_capture.write(f"Script Error: {e}\n")
            messagebox.showerror("Script Error", f"An error occurred in your script: {e}")

    def replace_script_tags(self, text):
        """
        Replace <@script> tags with the latest output.

        This function searches the input text for <@script> tags and replaces
        them with the most recent output captured by the script execution.

        Args:
            text (str): The input text containing <@script> tags.

        Returns:
            str: The modified text with <@script> tags replaced by the latest output.
        """
        while "<@script>" in text:
            latest_output = self.output_capture.read_latest_line()
            if latest_output:  # Only replace if there is new output.
                text = text.replace("<@script>", latest_output, 1)
                self.output_capture.clear()  # Clear the captured output after replacing.
        return text

    def save_inputs(self):
        """
        Save the current input values and the script content to the cache file.

        Args:
            None.

        Returns:
            None.
        """
        # Collect the input data
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

        # Get the script content from the script text area (assuming it's a Tkinter text widget)
        script_content = self.script_area.get("1.0", tk.END)  # Replace with the actual name of the script text widget

        # Call save_cache to save both the input data and the script content
        save_cache(data, script_content)


    def save_timestamp_options(self):
        """Function to save the selected timestamp option and custom timestamp.
        
        Args:
            None.

        Returns:
            None.
        """
        timestamp_data = {
            "timestamp_type": self.timestamp_type.get(),
            "custom_timestamp": self.custom_timestamp.get()
        }
        save_cache(timestamp_data)

    def on_close(self):
        """
        Ensure everything stops gracefully when closing the app.

        Args:
            None.

        Returns:
            None.
        """
        self.save_inputs()  # Save inputs to cache before closing.
        self.stop_rpc()  # Disconnect the Rich Presence.
        self.icon.stop()
        self.root.quit()
        if self.script_thread and self.script_thread.is_alive():
            # Gracefully terminate the script thread (if it's running).
            self.running = False
            self.script_thread.join(timeout=5)  # Wait up to 5 seconds for it to finish.
        self.root.quit()  # Close the application.

if __name__ == "__main__":
    root = ctk.CTk()
    app = CustomRichPresenceApp(root)
    root.mainloop()