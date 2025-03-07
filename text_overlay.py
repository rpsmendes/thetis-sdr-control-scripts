import pygetwindow as gw
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
import sys
import multiprocessing
import queue

class OverlayMenu(QWidget):
    def __init__(self, options, on_select_callback):
            super().__init__()
            self.options = options
            self.current_index = 0
            self.on_select_callback = on_select_callback
            self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(200, 150)

        self.layout = QVBoxLayout()
        self.label = QLabel("\n".join(self.get_menu_display()), self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def get_menu_display(self):
        return [f"> {opt} <" if i == self.current_index else opt for i, opt in enumerate(self.options)]

    def update_display(self):
        self.label.setText("\n".join(self.get_menu_display()))

    def navigate(self, direction):
        self.current_index = (self.current_index + direction) % len(self.options)
        self.update_display()

    def select_option(self):
        selected_option = self.options[self.current_index]
        self.on_select_callback(selected_option)  # Trigger callback with selected option
        self.hide()  # Hide the menu after selection

class OverlayManager(QObject):
    update_text_signal = pyqtSignal(str)
    show_menu_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.overlay = QLabel("")
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 180); color: white; font-size: 20px; padding: 20px; border-radius: 10px;")
        self.overlay.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overlay.resize(300, 100)
        self.overlay.move(800, 500)

        # Create a QTimer for hiding the overlay after the last message
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.overlay.hide)

        # Make the window not show in the taskbar
        self.overlay.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        # Menu overlay is initially None
        self.menu_overlay = None 
        self.show_menu_signal.connect(self.show_menu)

        self.update_text_signal.connect(self.update_text)

    def update_text(self, message):
        """Updates the overlay text and auto-hides after 1 second."""
        # Set the overlay's style (transparency and text styling)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 180); color: white; font-size: 20px; padding: 20px; border-radius: 10px;")
        
        # Set the overlay to always be on top and not show in the taskbar
        self.overlay.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        
        
        # Set the transparency level (80% opacity)
        self.overlay.setWindowOpacity(0.8)  # 80% opacity
        position_overlay(self.overlay)
        self.overlay.setText(message)
        self.overlay.show()

        # Reset the timer to hide after the specified time (e.g., 6 seconds)
        self.hide_timer.start(4000)

    def show_menu(self):
        if self.menu_overlay is None:
            menu_options = ["VFO B Control", "Volume Control", "Option 3"]
            self.menu_overlay = OverlayMenu(menu_options, self.handle_menu_selection)
            self.menu_overlay.show()

    def handle_menu_selection(self, selected_option):
        print(f"Selected option: {selected_option}")
        # Add logic for each option (e.g., VFO B control, volume control)

def position_overlay(overlay):
    """Position the overlay on the same screen where Thetis SDR is displayed."""
    thetis_pos = get_thetis_window_position()
    if thetis_pos:
        thetis_x, thetis_y, screen_width, screen_height = thetis_pos

        

        # Position the overlay to the same screen as Thetis window
        overlay.resize(300, 100)
        overlay.move(thetis_x + (screen_width - 300) // 2, thetis_y + screen_height - 200)  # 20px margin from the bottom

def get_thetis_window_position():
    """Find Thetis window and get its position."""
    thetis_window = None
    # Iterate through all open windows to find Thetis window by title
    for window in gw.getWindowsWithTitle('Thetis'):
            if window.title.startswith("Thetis") and "x64" in window.title and window.visible:
                thetis_window = window
                break

    if thetis_window:
        return thetis_window.left, thetis_window.top, thetis_window.size.width, thetis_window.size.height
    else:
        print("Thetis window not found!")
        return None

def overlay_process(message_queue):
    """Runs the PyQt application in a separate process."""
    app = QApplication(sys.argv)
    overlay_manager = OverlayManager()

    def check_queue():
        try:
            while True:
                message = message_queue.get_nowait()  # Get message from queue
                if message == "show_menu":
                    overlay_manager.show_menu_signal.emit()  # Show the menu overlay
                else:
                    overlay_manager.update_text_signal.emit(message)
        except queue.Empty:
            pass
        QTimer.singleShot(100, check_queue)  # Check queue every 100ms

    check_queue()  # Start checking messages
    sys.exit(app.exec())

# Global variables for communication
overlay_queue = multiprocessing.Queue()
overlay_proc = None

def start_overlay():
    """Starts the overlay process if not already running."""
    global overlay_proc
    if overlay_proc is None or not overlay_proc.is_alive():
        overlay_proc = multiprocessing.Process(target=overlay_process, args=(overlay_queue,))
        overlay_proc.start()

def show_overlay(message):
    """Sends a message to the overlay process."""
    if overlay_proc and overlay_proc.is_alive():
        overlay_queue.put(message)
    else:
        print("Overlay process is not running. Starting now...")
        start_overlay()
        overlay_queue.put(message)

# Main logic to simulate knob button press
def on_knob_button_press():
    """Called when the knob button is pressed."""
    show_overlay("show_menu")  # Send the show_menu message to the overlay process

# ✅ Only execute when running as main
if __name__ == "__main__":
    multiprocessing.freeze_support()  # Important for Windows!
    start_overlay()
    on_knob_button_press()
