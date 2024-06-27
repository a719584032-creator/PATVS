from pynput import mouse

# 定义一个回调函数，当鼠标被点击时调用
def monitor_keystrokes(cycles):
    click_count = 0

    def on_click(x, y, button, pressed):
        nonlocal click_count
        click_count += 1
        print(f"Mouse clicked at ({x}, {y}) with {button}. Total count: {click_count}")
        if click_count >= cycles:
            print("Reached target keystroke count. Exiting...")
            return False  # Stop the listener

    # Collect events until the target keystroke count is reached
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()



if __name__ == "__main__":
    target_keystrokes = 10  # Set the target number of keystrokes
    monitor_keystrokes(target_keystrokes)
