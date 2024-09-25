from pynput import keyboard


# 定义按键映射字典，将用户友好的名称映射到 pynput 的按键
KEY_MAPPING = {
    'alt': keyboard.Key.alt,
    'alt_l': keyboard.Key.alt_l,
    'alt_r': keyboard.Key.alt_r,
    'alt_gr': keyboard.Key.alt_gr,
    'backspace': keyboard.Key.backspace,
    'caps_lock': keyboard.Key.caps_lock,
    'cmd': keyboard.Key.cmd,
    'cmd_l': keyboard.Key.cmd_l,
    'cmd_r': keyboard.Key.cmd_r,
    'ctrl': keyboard.Key.ctrl,
    'ctrl_l': keyboard.Key.ctrl_l,
    'ctrl_r': keyboard.Key.ctrl_r,
    'delete': keyboard.Key.delete,
    'down': keyboard.Key.down,
    'end': keyboard.Key.end,
    'enter': keyboard.Key.enter,
    'esc': keyboard.Key.esc,
    'f1': keyboard.Key.f1,
    'f2': keyboard.Key.f2,
    'f3': keyboard.Key.f3,
    'f4': keyboard.Key.f4,
    'f5': keyboard.Key.f5,
    'f6': keyboard.Key.f6,
    'f7': keyboard.Key.f7,
    'f8': keyboard.Key.f8,
    'f9': keyboard.Key.f9,
    'f10': keyboard.Key.f10,
    'f11': keyboard.Key.f11,
    'f12': keyboard.Key.f12,
    'f13': keyboard.Key.f13,
    'f14': keyboard.Key.f14,
    'f15': keyboard.Key.f15,
    'home': keyboard.Key.home,
    'left': keyboard.Key.left,
    'page_down': keyboard.Key.page_down,
    'page_up': keyboard.Key.page_up,
    'right': keyboard.Key.right,
    'shift': keyboard.Key.shift,
    'shift_l': keyboard.Key.shift_l,
    'shift_r': keyboard.Key.shift_r,
    'space': keyboard.Key.space,
    'tab': keyboard.Key.tab,
    'up': keyboard.Key.up,
    'media_play_pause': keyboard.Key.media_play_pause,
    'media_volume_mute': keyboard.Key.media_volume_mute,
    'media_volume_down': keyboard.Key.media_volume_down,
    'media_volume_up': keyboard.Key.media_volume_up,
    'media_previous': keyboard.Key.media_previous,
    'media_next': keyboard.Key.media_next,
    'insert': keyboard.Key.insert,
    'menu': keyboard.Key.menu,
    'num_lock': keyboard.Key.num_lock,
    'pause': keyboard.Key.pause,
    'prtsc': keyboard.Key.print_screen,
    'scrlk': keyboard.Key.scroll_lock,
    'a': keyboard.KeyCode.from_char('a'),
    'b': keyboard.KeyCode.from_char('b'),
    'c': keyboard.KeyCode.from_char('c'),
    'd': keyboard.KeyCode.from_char('d'),
    'e': keyboard.KeyCode.from_char('e'),
    'f': keyboard.KeyCode.from_char('f'),
    'g': keyboard.KeyCode.from_char('g'),
    'h': keyboard.KeyCode.from_char('h'),
    'i': keyboard.KeyCode.from_char('i'),
    'j': keyboard.KeyCode.from_char('j'),
    'k': keyboard.KeyCode.from_char('k'),
    'l': keyboard.KeyCode.from_char('l'),
    'm': keyboard.KeyCode.from_char('m'),
    'n': keyboard.KeyCode.from_char('n'),
    'o': keyboard.KeyCode.from_char('o'),
    'p': keyboard.KeyCode.from_char('p'),
    'q': keyboard.KeyCode.from_char('q'),
    'r': keyboard.KeyCode.from_char('r'),
    's': keyboard.KeyCode.from_char('s'),
    't': keyboard.KeyCode.from_char('t'),
    'u': keyboard.KeyCode.from_char('u'),
    'v': keyboard.KeyCode.from_char('v'),
    'w': keyboard.KeyCode.from_char('w'),
    'x': keyboard.KeyCode.from_char('x'),
    'y': keyboard.KeyCode.from_char('y'),
    'z': keyboard.KeyCode.from_char('z'),
    '`': keyboard.KeyCode.from_char('`'),
    '1': keyboard.KeyCode.from_char('1'),
    '2': keyboard.KeyCode.from_char('2'),
    '3': keyboard.KeyCode.from_char('3'),
    '4': keyboard.KeyCode.from_char('4'),
    '5': keyboard.KeyCode.from_char('5'),
    '6': keyboard.KeyCode.from_char('6'),
    '7': keyboard.KeyCode.from_char('7'),
    '8': keyboard.KeyCode.from_char('8'),
    '9': keyboard.KeyCode.from_char('9'),
    '0': keyboard.KeyCode.from_char('0'),
    '-': keyboard.KeyCode.from_char('-'),
    '=': keyboard.KeyCode.from_char('='),
    '[': keyboard.KeyCode.from_char('['),
    ']': keyboard.KeyCode.from_char(']'),
    '\\': keyboard.KeyCode.from_char('\\'),  # 单反斜杠
    ';': keyboard.KeyCode.from_char(';'),
    ',': keyboard.KeyCode.from_char(','),
    '.': keyboard.KeyCode.from_char('.'),
    '/': keyboard.KeyCode.from_char('/')
}

def monitor_keystrokes(cycles,  key_name=None):
    key_count = 0
    key = KEY_MAPPING.get(key_name.lower()) if key_name else None
    def on_press(pressed_key):
        nonlocal key_count
        if key is None or pressed_key == key:
            key_count += 1
            print(f"Key pressed: {pressed_key}. Total count: {key_count}")
            if key_count >= cycles:
                print("Reached target keystroke count. Exiting...")
                return False  # Stop the listener

    # Collect events until the target keystroke count is reached
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

stop_event = True
def monitor_keystrokes2(target_cycles):
    key_count = 0
    while stop_event:
        def on_press(key):
            nonlocal key_count
            key_count += 1
            print(f"Key pressed: {key}. Total count: {key_count}")

            if key_count >= target_cycles:
                print("Reached target keystroke count. Exiting...")

                return False  # Stop the listener


        # Collect events until the target keystroke count is reached
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

if __name__ == "__main__":
    monitor_keystrokes2(100)
