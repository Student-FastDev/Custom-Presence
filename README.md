# Custom Presence

Python-based GUI application designed to and manage Discord Rich Presence features.

## Prerequisites

Before setting up the **Custom Discord Rich Presence Manager**, ensure you have the following installed:

- **Python:** Version 3.6 or higher. [Download Python](https://www.python.org/downloads/).
- **Git:** For cloning the repository. [Download Git](https://git-scm.com/downloads).
- **Discord Account:** To utilize Discord Rich Presence features. [Sign Up for Discord](https://discord.com/).

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

3. **Timestamp Settings:**

    - **Options:** Select from various timestamp types, including custom delays and specific time formats.

## Notes

- **Security:** Handle your Discord App ID and any sensitive information securely. Avoid sharing credentials or exposing sensitive data within scripts.
---

<div align="center">  
    <img src="https://cdn.prod.website-files.com/6257adef93867e50d84d30e2/636e0a6a49cf127bf92de1e2_icon_clyde_blurple_RGB.png" alt="Chrome Logo" width="50px">
</div>
