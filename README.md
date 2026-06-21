# Custom Presence

Python-based GUI application designed to manage Discord Rich Presence features.

## Prerequisites

To run the Custom Presence application, ensure you have the following installed:

- **Python:** Version 3.6 or higher.
- **Git:** For cloning the repository.
- **Discord Account:** To utilize Discord Rich Presence features.

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

2. **Configure Settings:**

    Configure your Rich Presence directly within the application's interface:

    - **App ID:** Enter your Discord application's Client ID. You can obtain this from the Discord Developer Portal.
    - **Details & State:** Customize the `Details` and `State` fields to display specific information in your Discord status.
    - **Party Size:** Set the current and maximum party size if applicable.
    - **Images:** Add keys and texts for large and small images to enhance your Rich Presence visuals.
    - **Buttons:** Configure up to two interactive buttons with custom labels and URLs.
    - **Timestamp:** Choose the type of timestamp to display, such as local time, custom timestamp, or since the program started.

## Notes

- **Cache Management:** User inputs and scripts are saved to `cache.json` to preserve settings between sessions. Avoid manually editing the cache file to prevent data corruption. Use the application interface to modify settings.
- **Custom Scripts:** Utilize the `OutputCapture` class to redirect and display script outputs within the application. Ensure that your custom scripts are safe and free from malicious code to prevent unintended behavior. Example script:

    ```python
    import time

    for i in range(1, 11):
        print(i) # Update the presence.
        time.sleep(10)  # Pause for 10 seconds.
    ```

---

<div align="center">  
    <img src="https://cdn.prod.website-files.com/6257adef93867e50d84d30e2/636e0a6a49cf127bf92de1e2_icon_clyde_blurple_RGB.png" alt="Chrome Logo" width="50px">
</div>
