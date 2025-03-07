import time
import math
import sys
import subprocess
from cat_command import send_cat_command  # Import the function

try:
    import mido
    import rtmidi
    import tkinter as tk
    from tkinter import Label
except ModuleNotFoundError:
    print("Module 'mido' not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mido"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-rtmidi"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tkinter"])
    import mido  # Retry import after installation
    import rtmidi
    import tkinter as tk
    from tkinter import Label

# print(mido.get_input_names())
# MIDI Device Name (Run `mido.get_input_names()` to check available names)
MIDI_DEVICE_NAME = "LPD8 1"  # Adjust to match your MIDI device
# Global Tkinter Window
root = None
label = None
gTime = time.time()

# Mapping of MIDI Notes/CC to CAT Commands
# MIDI_TO_CAT = {
#     1: "ZZAD04;",  # C1 - Set frequency Up 100Hz
#     2: "ZZAu04;",  # C#1 - Set frequency Down 100Hz
# }

MIDI_TO_CAT = {
    # Knob Buttons - key: {command, scale}
    101: {"command": "ZZLA", "scale": 100}, # RX1 Voume
    102: {"command": "ZZLB", "scale": 100}, # Sets or reads the RX0 Stereo Balance (MultiRX Group Controls)
    103: {"command": "ZZLD", "scale": 100}, # Sets or reads the RX1 Stereo Balance (MultiRX Group Controls) 
    104: {"command": "ZZLC", "scale": 100}, # Sets or reads the RX2 Stereo Balance
    105: {"command": "ZZTO", "scale": 100}, # Sets or reads the TUN power setting 
    106: {"command": "ZZFL", "scale": 9999}, # Sets or reads Selected RX1 DSP Filter Low P1 = frequency in Hz -9999 to 09999.
    107: {"command": "ZZFH", "scale": 9999}, # Sets or reads Selected RX1 DSP Filter High P1 = frequency in Hz -9999 to 09999.
    108: {"command": "ZZIT", "scale": 1000}, # Sets or reads the variable filter shift slider - ZZIT P1 P2 P2 P2 P2 ; P1 = “+” or “-“; P2 = 0000 to 1000 (-1000 to +1000)
}

MIDI_TO_CAT_MOMENTARY = {
    "25-note_on": "ZZTX1;",  # MOX On
    "25-note_off": "ZZTX0;",  # MOX Off
    "29-note_on": "ZZTX1;", # MOX On Momentary
    "29-note_off": "ZZTX0;", # MOX Off Momentary
    "26-note_on": "ZZTU1;", # TUN On
    "26-note_off": "ZZTU0;", # TUN Off
    "32-note_on": "ZZIU;", # ZZIU Resets the variable filter shift slider 
    0: "ZZBS160;", # ZZBS Sets or reads the RX1 Band Switch - 160m
    1: "ZZBS080;", # ZZBS Sets or reads the RX1 Band Switch - 80m
    2: "ZZBS040;", # ZZBS Sets or reads the RX1 Band Switch - 40m
    3: "ZZBS020;", # ZZBS Sets or reads the RX1 Band Switch - 20m
    4: "ZZBS017;", # ZZBS Sets or reads the RX1 Band Switch - 17m
    5: "ZZBS015;", # ZZBS Sets or reads the RX1 Band Switch - 15m
    6: "ZZBS012;", # ZZBS Sets or reads the RX1 Band Switch - 12m
    7: "ZZBS010;", # ZZBS Sets or reads the RX1 Band Switch - 10m
}

# Function to Show the Indicator
def show_indicator(text, start_time):
    global root, label, gTime

    if gTime - start_time < 3:
        if root is None:
            root = tk.Tk()
            root.overrideredirect(True)  # Hide window decorations
            root.attributes('-topmost', True)  # Always on top
            root.geometry("200x100+50+50")  # Position on screen
            root.configure(bg="black")
            
            label = Label(root, text="", font=("Arial", 20), fg="white", bg="black")
            label.pack(expand=True)

        label.config(text=text)
        root.deiconify()  # Show the window
        root.update()

        # Hide window after 1 second
        root.after(1000, root.withdraw)
        gTime = time.time()


def calculate_sleep_time(value):
    """Calculate sleep time using an inverse exponential function."""
    value = max(1, min(value, 127))  # Ensure value is within 1-127

    A = 0.20  # Sleep time for value = 1
    B = 0.0510  # Decay factor

    sleep_time = A * math.exp(-B * (value - 1))
    return sleep_time

# Keep track of active keys
last_cmd = []
velocity = 0.05

def convert_to_hundred_scale(value):
    result = math.floor((value * 100) / 127)
    return f"{result:03d}"

def convert_to_mod_scale(value, scale):
    # Scale range [0, 64] to [-scale, 0]
    if 0 <= value <= 64:
        scaled_value = scale - math.floor((value / 64) * scale)
        return f"-{scaled_value:04d}"  # Make it negative

    # Scale range [66, 126] to [0, scale]
    elif 66 <= value <= 126:
        scaled_value = math.floor(((value - 66) / (126 - 66)) * scale)
        return f"{scaled_value:05d}"


def midi_listener():
    """ Listens for MIDI input and processes commands. """
    print(f"🎛️ Listening for MIDI input from {MIDI_DEVICE_NAME}...")
    
    try:
        with mido.open_input(MIDI_DEVICE_NAME) as midi_in:
            for msg in midi_in:
                if hasattr(msg, "note"):
                    print(msg)
                    # Pad buttons
                    key = f"{msg.note}-{msg.type}"
                    if key in MIDI_TO_CAT_MOMENTARY:
                            cat_cmd = MIDI_TO_CAT_MOMENTARY[key]
                            send_cat_command(cat_cmd)
                    
                elif (msg.type == "program_change"):
                    key = msg.program
                    cat_cmd = MIDI_TO_CAT_MOMENTARY[key]
                    send_cat_command(cat_cmd)
                    print(msg)
                else:
                    # Knob Buttons
                    # print(vars(msg))
                    key = msg.control
                    if key in MIDI_TO_CAT and msg.value % 4 == 0:
                        scale = MIDI_TO_CAT[key]["scale"]
                        match scale:
                            case 100:
                                value =  convert_to_hundred_scale(msg.value)
                            case _:
                                value =  convert_to_mod_scale(msg.value, scale)

                        cat_cmd = f"{MIDI_TO_CAT[key]["command"]}{value};"
                        send_cat_command(cat_cmd)


                        # time.sleep(0.1)  # Small delay to prevent excessive CPU usage

    except KeyboardInterrupt:
        print("\n🛑 Script exited by user.")

if __name__ == "__main__":
    midi_listener()
