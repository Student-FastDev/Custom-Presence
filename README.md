# Custom Discord Rich Presence Manager

**Custom Discord Rich Presence Manager** is a Python-based GUI application designed to seamlessly integrate and manage Discord Rich Presence features. Leveraging libraries like `customtkinter`, `pypresence`, and `pystray`, this tool offers a user-friendly interface to customize your Discord status with detailed information, images, and interactive buttons. Additionally, it supports executing custom Python scripts to enhance functionality and automate tasks.

## Features

- **User-Friendly GUI:** Intuitive interface built with `customtkinter` for easy configuration of Rich Presence settings.
- **Discord Rich Presence Integration:** Connect and update your Discord status with customizable details, state, images, and buttons.
- **Custom Scripting:** Embed and execute custom Python scripts directly within the application to extend functionality.
- **System Tray Integration:** Minimize the application to the system tray with options to show the window, connect/disconnect Rich Presence, and exit the application.
- **Output Capture:** Capture and display script output within the application, enhancing debugging and monitoring.
- **Cache Management:** Save and load user inputs and scripts using a cache file to preserve settings between sessions.
- **Syntax Highlighting:** Real-time syntax highlighting in the script editor for improved readability and development experience.
- **Fade-In Animation:** Smooth fade-in effect for the application window upon startup.

## Prerequisites

Before setting up the **Custom Discord Rich Presence Manager**, ensure you have the following installed:

- **Python:** Version 3.6 or higher. [Download Python](https://www.python.org/downloads/)
- **Git:** For cloning the repository. [Download Git](https://git-scm.com/downloads)
- **Discord Account:** To utilize Discord Rich Presence features. [Sign Up for Discord](https://discord.com/)

## Installation

1. **Clone the Repository:**

    ```sh
    git clone https://github.com/Student-FastDev/Custom-Presence/
    cd Custom-Presence
    ```

2. **Install Required Packages:**

    Install the necessary Python packages using `pip`:

    ```sh
    pip install -r requirements.txt
    ```

    **Required Packages:**

    - `customtkinter`
    - `pypresence`
    - `pystray`
    - `Pillow`
    - `pystray`
    - `asyncio`


## Usage

1. **Run the Application:**

    Execute the main script to launch the GUI:

    ```bash
    python presence.py
    ```

2. **Configure Rich Presence Settings:**

    - **App ID:** Enter your Discord application's Client ID. You can obtain this from the [Discord Developer Portal](https://discord.com/developers/applications).
    - **Details & State:** Customize the `Details` and `State` fields to display specific information in your Discord status.
    - **Party Size:** (Optional) Set the current and maximum party size if applicable.
    - **Images:** Add keys and texts for large and small images to enhance your Rich Presence visuals.
    - **Buttons:** Configure up to two interactive buttons with custom labels and URLs.
    - **Timestamp:** Choose the type of timestamp to display, such as local time, custom timestamp, or since the program started.

3. **Execute Custom Scripts:**

    - **Script Editor:** Write or paste your custom Python scripts in the provided script area.
    - **Syntax Highlighting:** Enjoy real-time syntax highlighting for better readability and error detection.
    - **Run Scripts:** Scripts execute automatically when Rich Presence is connected. Monitor output and errors within the application.

4. **System Tray Management:**

    - **Minimize to Tray:** Click the background toggle button to hide the window and keep the tray icon active.
    - **Tray Menu:** Access options like showing the window, connecting/disconnecting Rich Presence, and exiting the application directly from the tray icon.

## Configuration

1. **Cache Management:**

    - **Cache File:** User inputs and scripts are saved to `cache.json` to preserve settings between sessions.
    - **Editing Cache:** Avoid manually editing the cache file to prevent data corruption. Use the application interface to modify settings.

2. **Custom Scripts:**

    - **Accessing Outputs:** Utilize the `OutputCapture` class to redirect and display script outputs within the application.
    - **Security:** Ensure that your custom scripts are safe and free from malicious code to prevent unintended behavior.

    <br>
    
    ```python
    import time

    for i in range(1, 11):
        print(i) # Update the presence.
        time.sleep(10)  # Pause for 10 seconds.
    ```

4. **Timestamp Settings:**

    - **Options:** Select from various timestamp types, including custom delays and specific time formats.
    - **Validation:** The application validates timestamp inputs to ensure correct formatting and functionality.

## Notes

- **Asynchronous Efficiency:** While the current version uses threading for script execution and Rich Presence updates, future updates may incorporate asynchronous programming (`asyncio`) to enhance performance.
  
- **Proxy Support:** Proxy integration is planned for future releases to enhance privacy and security during web automation tasks.
  
- **Security:** Handle your Discord App ID and any sensitive information securely. Avoid sharing credentials or exposing sensitive data within scripts.
---

<div align="center">  
    <img src="https://cdn.prod.website-files.com/6257adef93867e50d84d30e2/636e0a6a49cf127bf92de1e2_icon_clyde_blurple_RGB.png" alt="Chrome Logo" width="50px">
</div>
