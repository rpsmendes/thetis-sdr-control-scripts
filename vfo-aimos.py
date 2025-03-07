from enum import Enum
from pynput import keyboard
from cat_command import send_cat_command, query_cat
from text_overlay import show_overlay, on_knob_button_press
import logging
import threading
import time
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MenuFunctions(Enum):
    CONTROL_VFO_A = ("VFO A \n Control")
    CONTROL_VFO_B = ("VFO B \n Control")
    VOLUME_VFO_A = ("VFO A \n Volume")
    VOLUME_VFO_B = ("VFO B \n Volume")

    def __str__(self):
        return self.value  # Access the first (only) tuple element

    # @property
    # def step_id(self):
    #     return self.value[1]

    # @property
    # def vfo(self):
    #     return self.value[2]

class MenuToogle(Enum):
    ON = True
    OFF = False

    # Function to get MenuToggle by boolean value
    def switch(value):
        return MenuToogle.ON if value == MenuToogle.OFF else MenuToogle.ON

class CATCommand(str, Enum):
    CONTROL_VFO_A = "ZZSW0;"    # Sets VFO A TX Buttons
    CONTROL_VFO_B = "ZZSW1;"    # Sets VFO B TX Buttons    
    TUNE_STEP_1 = "ZZAC00;"     # Sets the Step Size 
    TUNE_STEP_10 = "ZZAC02;"    # Sets the Step Size 
    TUNE_STEP_50 = "ZZAC04;"    # Sets the Step Size 
    TUNE_STEP_100 = "ZZAC05;"   # Sets the Step Size 
    TUNE_STEP_500 = "ZZAC07;"   # Sets the Step Size 
    TUNE_STEP_1K = "ZZAC08;"    # Sets the Step Size 
    TUNE_STEP_5K = "ZZAC11;"    # Sets the Step Size 
    TUNE_STEP_SIZE = "ZZAC;"    # Reads the Step Size 
    VFO_A_FREQ = "ZZFA"         # Sets or reads VFO A frequency
    VFO_A_FREQ_UP = "ZZSB;"     # Moves VFO A up one Tune Step
    VFO_A_FREQ_DOWN = "ZZSA;"     # Moves VFO A down one Tune Step

class CircularIterator:
    def __init__(self, data):
        """ Initializes the circular iterator with the provided dictionary. """
        self.data = data
        self.keys = list(data.keys())  # List of keys for iteration
        self.current_index = 0  # Default starting index (can be set later)

    def start_from(self, key):
        """ Set the start point for iteration from a given key. """
        self.current_index = self.keys.index(key)
        return self

    def next(self):
        """ Move to the next item in the circular dictionary. """
        current_key = self.keys[self.current_index]
        current_value = self.data[current_key]
        # Move to the next index, wrapping around using modulo
        self.current_index = (self.current_index + 1) % len(self.keys)
        return current_key, current_value

    def previous(self):
        """ Move to the previous item in the circular dictionary. """
        current_key = self.keys[self.current_index]
        current_value = self.data[current_key]
        # Move to the previous index, wrapping around using modulo
        self.current_index = (self.current_index - 1) % len(self.keys)
        return current_key, current_value

    def current(self):
        """ Get the current item (key and value) without changing the state. """
        current_key = self.keys[self.current_index]
        current_value = self.data[current_key]
        return current_key, current_value

BUTTON_MENU = {
    0: {"menu_function":MenuFunctions.CONTROL_VFO_A, "vfo_control_cmd": CATCommand.CONTROL_VFO_A},
    1: {"menu_function":MenuFunctions.CONTROL_VFO_B, "vfo_control_cmd": CATCommand.CONTROL_VFO_B},
    2: {"menu_function":MenuFunctions.VOLUME_VFO_A, "vfo_control_cmd":""},
    2: {"menu_function":MenuFunctions.VOLUME_VFO_B, "vfo_control_cmd":""},

}

TUNE_STEPS = {
    0: {"step": 1, "cmd": CATCommand.TUNE_STEP_1, "active": True, "step_text":"1Hz"},    # 1 Hz
    1: {"step": 2, "cmd": "ZZAC01;", "active": False, "step_text":"2Hz"},    # 2 Hz
    2: {"step": 10, "cmd": CATCommand.TUNE_STEP_10, "active": True, "step_text":"10Hz"},   # 10 Hz
    3: {"step": 25, "cmd": "ZZAC03;", "active": False, "step_text":"25Hz"},   # 25 Hz
    4: {"step": 50, "cmd": CATCommand.TUNE_STEP_50, "active": True, "step_text":"50Hz"},   # 50 Hz
    5: {"step": 100, "cmd": CATCommand.TUNE_STEP_100, "active":True, "step_text":"100Hz"},  # 100 Hz
    6: {"step": 250, "cmd": "ZZAC06;", "active": False, "step_text":"250Hz"},  # 250 Hz
    7: {"step": 500, "cmd": CATCommand.TUNE_STEP_500, "active": True, "step_text":"500Hz"},  # 500 Hz
    8: {"step": 1000, "cmd": CATCommand.TUNE_STEP_1K, "active": True, "step_text":"1KHz"}, # 1 KHz
    9: {"step": 2000, "cmd": "ZZAC09;", "active": False, "step_text":"2KHz"}, # 2 KHz
    10: {"step": 2500, "cmd": "ZZAC10;", "active": False, "step_text":"2.5KHz"}, # 2.5 KHz
    11: {"step": 5000, "cmd": CATCommand.TUNE_STEP_5K, "active": True, "step_text":"5KHz"},  # 5 KHz
    12: {"step": 6250, "cmd": "ZZAC12;", "active": False, "step_text":"6.25KHz"},  # 6.25 KHz
    13: {"step": 9000, "cmd": "ZZAC13;", "active": False, "step_text":"9KHz"},  # 9 KHz
    14: {"step": 10000, "cmd": "ZZAC14;", "active": False, "step_text":"10KHz"}, # 10 KHz
    15: {"step": 12500, "cmd": "ZZAC15;", "active": False, "step_text":"12.5KHz"}, # 12.5 KHz
    16: {"step": 15000, "cmd": "ZZAC16;", "active": False, "step_text":"15KHz"}, # 15 KHz
    17: {"step": 20000, "cmd": "ZZAC17;", "active": False, "step_text":"20KHz"}, # 20 KHz
    18: {"step": 25000, "cmd": "ZZAC18;", "active": False, "step_text":"25KHz"}, # 25 KHz
    19: {"step": 30000, "cmd": "ZZAC19;", "active": False, "step_text":"30KHz"}, # 30 KHz
    20: {"step": 50000, "cmd": "ZZAC20;", "active": False, "step_text":"50KHz"}, # 50 KHz
    21: {"step": 100000, "cmd": "ZZAC21;", "active": False, "step_text":"100KHz"}, # 100 KHz
    22: {"step": 250000, "cmd": "ZZAC22;", "active": False, "step_text":"250KHz"}, # 250 KHz
    23: {"step": 500000, "cmd": "ZZAC23;", "active": False, "step_text":"500KHz"}, # 500 KHz
    24: {"step": 1000000, "cmd": "ZZAC24;", "active": False, "step_text":"1MHz"}, # 1 MHz
    25: {"step": 10000000, "cmd": "ZZAC25;", "active": False, "step_text":"10MHz"}, # 10 MHz
}


# Define the keys you want to suppress
suppressed_keys = {
    177: {"msg": 256, "type": "stepTune", "direction": "up"},#keyboard.Key.media_next,
    176: {"msg": 256, "type": "stepTune", "direction": "down"},#keyboard.Key.media_previous,
    175: {"msg": 256, "type": "volume", "direction": "up"},#keyboard.Key.media_volume_up,
    174: {"msg": 256, "type": "volume", "direction": "down"},#keyboard.Key.media_volume_down,
    173: {"msg": 256, "type": "mute"},#keyboard.Key.media_volume_mute
}

# Global Variables
tune_step_iterator = CircularIterator(TUNE_STEPS)
menu_functions_iterator =  CircularIterator(BUTTON_MENU)
keyboard_controller = keyboard.Controller()
listener = None
step_has_changed = False
menu_toogle = MenuToogle.OFF

# data object coming from win32_event_filter(msg, data)
data_object = None

def send_command_in_thread(command: CATCommand, param:str = None):
    def run():
        try:
            logging.info(f"operation=send_command_in_thread, sending CAT cmd: {command}")
            cmd = command.value if not param else f"{command.value}{param};"
            send_cat_command(cmd)
        except Exception as e:
            logging.exception(f"operation=send_command_in_thread, error while sending CAT command: {e}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

def get_tune_step_cmd(key):
    global tune_step_iterator
    current_value = query_cat(CATCommand.TUNE_STEP_SIZE.value)
    last_two_digits = int(current_value[-2:])

    if key in suppressed_keys:
        match suppressed_keys[key]:
            case {"direction": "down"}:
                tune_step_iterator.start_from(last_two_digits).next()
                while True:
                    next = tune_step_iterator.next()
                    if next[1]["active"] == True:
                        show_overlay(f"Step tune {next[1]["step_text"]}")
                        logging.info(f"operation=get_tune_step_cmd, getting cmd {next[1]["cmd"]} for key {key}")
                        return next[1]["cmd"]

            case {"direction": "up"}:
                tune_step_iterator.start_from(last_two_digits).previous()
                while True:
                    previous = tune_step_iterator.previous()
                    if previous[1]["active"] == True:
                        show_overlay(f"Step tune {previous[1]["step_text"]}")
                        logging.info(f"operation=get_tune_step_cmd, getting cmd {previous[1]["cmd"]} for key {key}")
                        return previous[1]["cmd"]

def reset_vfo_a_last_three_digits(direction):
    # Retrieve the current frequency of VFO A
    current_freq_str = query_cat(CATCommand.VFO_A_FREQ.value)
    
    # Convert the frequency string to an integer
    try:
        current_freq = int(current_freq_str[-11:])
    except ValueError:
        logging.exception(f"operation=reset_vfo_a_last_three_digits, Invalid frequency received: {current_freq_str}")
        return False
    
    # Check if the last three digits are '000'
    if current_freq % 1000 == 0:
        return False
    
    # Calculate the new frequency based on the direction
    if direction == "up":
        # Find the nearest '000' above the current frequency
        new_freq = ((current_freq + 999) // 1000) * 1000
    elif direction == "down":
        # Find the nearest '000' below the current frequency
        new_freq = (current_freq // 1000) * 1000
    else:
        print(f"Invalid direction: {direction}")
        return False
    
    # Format the new frequency as a 10-digit string with leading zeros
    new_freq_str = f"{new_freq:011d}"
    
    # Send the new frequency to VFO A
    send_command_in_thread(CATCommand.VFO_A_FREQ, new_freq_str)
    return True

def get_current_tune_step():
    current_step_code = query_cat(CATCommand.TUNE_STEP_SIZE.value)
    try:
        current_step_code_int = int(current_step_code[-2:])
    except Exception as e:
        logging.error(f"operation=win32_event_filter, error converting current_step_code to int {e}")
        current_step_code_int = 0

    current_tune_step_value = TUNE_STEPS.get(current_step_code_int)["step"]
    return current_tune_step_value

def dispatch_cmd(key_code):
    global step_has_changed

    keys = suppressed_keys.get(key_code)
    match keys:
        case {"type": "stepTune"}:
            cmd = get_tune_step_cmd(key_code)
            send_command_in_thread(cmd)
            step_has_changed = True

        case {"type": "volume", "direction": "up"}:
            if step_has_changed:
                if not reset_vfo_a_last_three_digits("up"):
                    send_command_in_thread(CATCommand.VFO_A_FREQ_UP)
                    step_has_changed = False
            else:
                send_command_in_thread(CATCommand.VFO_A_FREQ_UP)

        case {"type": "volume", "direction": "down"}:
            if step_has_changed:
                if not reset_vfo_a_last_three_digits("down"): 
                    send_command_in_thread(CATCommand.VFO_A_FREQ_DOWN)
                    step_has_changed = False
            else:
                send_command_in_thread(CATCommand.VFO_A_FREQ_DOWN)

def check_menu_toogle_cmd(key_code):
    global menu_toogle

    if key_code == 173:
        menu_toogle = MenuToogle.switch(menu_toogle)
    
    return menu_toogle

# def handle_selection(option):
#     print(f"User selected: {option}")

#     options = ["Control VFO A", "Control VFO B", "Adjust Volume", "Settings"]
#     overlay = OverlayMenuWithOptions(options, handle_selection)
#     overlay.show()


##################################
### pynput functions defenition ##
##################################
def win32_event_filter(msg, data):
    global menu_toogle
    # Preventing double stroke from the knob controller.
    # Msg comes with 2 values: 256 and 257. Only processing the first, since the second would cause issuing double command.
    logging.debug(f"Filtering msg={msg}, data={data}")
    if msg == 256:

        logging.debug(f"operation=win32_event_filter, received key event: {msg}, data: {data}")

        key_code = data.vkCode  # Virtual key code
        logging.info(f"operation=win32_event_filter, key_code: {key_code}")
        print(menu_toogle)
        menu_toogle = check_menu_toogle_cmd(key_code)
        print(menu_toogle)
        match menu_toogle:
            case MenuToogle.ON:
                print("MENU ON")
                ## on_knob_button_press()
                # handle_selection("Control VFO A")
            case MenuToogle.OFF:
                print("MENU OFF")

        # Check if key should be suppressed
        if key_code in suppressed_keys:
            logging.info(f"operation=win32_event_filter, processing msg: {msg}")

            # Use regex to extract the memory address
            match = re.search(r"0x([0-9A-Fa-f]+)", str(data))

            if match:
                dispatch_cmd(key_code)
                logging.debug(f"operation=win32_event_filter, suppressing event for key: {key_code}")
                
                # Block key globally
                listener.suppress_event() 
                
                # Do not pass to on_press
                return False
            
        # Allow key event to propagate    
        return True

def start_listener():
    global listener
    global keyboard_controller
    logging.info("operation=start_listener, initializing listener...")
    show_overlay(f"{MenuFunctions.CONTROL_VFO_A}")
    # Start a new listener
    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
        suppress=False,
        win32_event_filter=win32_event_filter
    )
    try:
        listener.start()
        logging.info("operation=start_listener, listener started successfully")
    except Exception as e:
        logging.exception(f"operation=start_listener, listener failed to start: {e}")

def on_press(key):
    return True

def on_release(key):
    # Stop listener when escape key is pressed
    if key == keyboard.Key.esc:
        return False  # Stop listener
    
# Start the first listener at the beginning
# Ensure this block is under __name__ == '__main__':
if __name__ == "__main__":
    start_listener()

    try:
        while True:
            if listener and not listener.is_alive():
                logging.error("operation=main_loop, listener has stopped! Restarting...")
                start_listener()
            time.sleep(1)  # Prevent CPU overuse
    except KeyboardInterrupt:
        logging.info("operation=main_loop, shutting down due to KeyboardInterrupt")
        if listener:
            listener.stop()