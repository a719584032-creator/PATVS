from pynput import keyboard

def monitor_keystrokes(cycles):
    key_count = 0

    def on_press(key):
        nonlocal key_count
        key_count += 1
        print(f"Key pressed: {key}. Total count: {key_count}")
        if key_count >= cycles:
            print("Reached target keystroke count. Exiting...")
            return False  # Stop the listener

    # Collect events until the target keystroke count is reached
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    target_keystrokes = 10  # Set the target number of keystrokes
    monitor_keystrokes(target_keystrokes)
