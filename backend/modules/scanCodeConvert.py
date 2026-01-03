SCANCODE_MAP = {
    # --- Row 1 (Esc & F-Keys) ---
    0x01: "Esc",
    0x3B: "F1",
    0x3C: "F2",
    0x3D: "F3",
    0x3E: "F4",
    0x3F: "F5",
    0x40: "F6",
    0x41: "F7",
    0x42: "F8",
    0x43: "F9",
    0x44: "F10",
    0x57: "F11",
    0x58: "F12",

    # --- Row 2 (Number Row) ---
    0x29: "` ~",         # Tilde / Backtick
    0x02: "1",
    0x03: "2",
    0x04: "3",
    0x05: "4",
    0x06: "5",
    0x07: "6",
    0x08: "7",
    0x09: "8",
    0x0A: "9",
    0x0B: "0",
    0x0C: "- _",         # Minus / Underscore
    0x0D: "= +",         # Equals / Plus
    0x0E: "Backspace",

    # --- Row 3 (Tab & QWERTY) ---
    0x0F: "Tab",
    0x10: "Q",
    0x11: "W",
    0x12: "E",
    0x13: "R",
    0x14: "T",
    0x15: "Y",
    0x16: "U",
    0x17: "I",
    0x18: "O",
    0x19: "P",
    0x1A: "[ {",
    0x1B: "] }",
    0x2B: "|",        # Backslash (above Enter on ANSI)

    # --- Row 4 (Caps & ASDF) ---
    0x3A: "Caps Lock",
    0x1E: "A",
    0x1F: "S",
    0x20: "D",
    0x21: "F",
    0x22: "G",
    0x23: "H",
    0x24: "J",
    0x25: "K",
    0x26: "L",
    0x27: "; :",
    0x28: "\\",        # Quote
    0x1C: "Enter",

    # --- Row 5 (Shift & ZXCV) ---
    0x2A: "Left Shift",
    0x2C: "Z",
    0x2D: "X",
    0x2E: "C",
    0x2F: "V",
    0x30: "B",
    0x31: "N",
    0x32: "M",
    0x33: ", <",
    0x34: ". >",
    0x35: "/ ?",
    0x36: "Right Shift",

    # --- Row 6 (Modifiers & Space) ---
    0x1D: "Left Ctrl",
    0xE05B: "Left Win",
    0x38: "Left Alt",
    0x39: "Space",
    0xE038: "Right Alt",
    0xE05C: "Right Win",
    0xE05D: "Menu / App",
    0xE01D: "Right Ctrl",

    # --- System Keys ---
    0xE037: "Print Screen",
    0x46: "Scroll Lock",
    0xE11D: "Pause",     # Your custom canonical Pause mapping

    # --- Navigation Block ---
    0xE052: "Insert",
    0xE047: "Home",
    0xE049: "Page Up",
    0xE053: "Delete",
    0xE04F: "End",
    0xE051: "Page Down",
    0xE048: "Arrow Up",
    0xE04B: "Arrow Left",
    0xE050: "Arrow Down",
    0xE04D: "Arrow Right",

    # --- Numpad ---
    0x45: "Num Lock",
    0xE035: "Numpad /",
    0x37: "Numpad *",
    0x4A: "Numpad -",
    0x47: "Numpad 7",
    0x48: "Numpad 8",
    0x49: "Numpad 9",
    0x4E: "Numpad +",
    0x4B: "Numpad 4",
    0x4C: "Numpad 5",
    0x4D: "Numpad 6",
    0x4F: "Numpad 1",
    0x50: "Numpad 2",
    0x51: "Numpad 3",
    0xE01C: "Numpad Enter",
    0x52: "Numpad 0",
    0x53: "Numpad ."
}

SCANCODE_MAP_MOUSE = {
        0x0001: "left",
        0x0004: "right",
        0x0010: "middle",
        0x0040: "x1",
        0x0100: "x2",
    }

def scancode_to_key(scancode: int) -> str:
    return SCANCODE_MAP.get(scancode, f"Unknown (0x{scancode:X})")
