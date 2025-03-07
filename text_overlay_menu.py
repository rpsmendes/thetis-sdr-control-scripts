from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
import sys

class OverlayMenuWithOptions(QWidget):
    def __init__(self, options, on_select):
        super().__init__()
        self.options = options
        self.on_select = on_select  # Callback function for selection
        self.current_index = 0  # Track the selected option
        self.initUI()
    
    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 300)  # Increased size
        
        self.layout = QVBoxLayout()
        self.label = QLabel("\n".join(self.get_menu_display()), self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 20px; color: white;")  # Bigger text
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
        if self.on_select:
            self.on_select(selected_option)  # Call the provided callback function
        self.hide()  # Hide the overlay after selection
    
if __name__ == "__main__":
    def handle_selection(option):
        print(f"Selected: {option}")
    
    app = QApplication.instance()  # Check if an instance already exists
    if not app:  # Create one only if it does not exist
        app = QApplication(sys.argv)

    options = ["Control VFO A", "Control VFO B", "Adjust Volume", "Settings"]
    overlay = OverlayMenuWithOptions(options, handle_selection)
    overlay.show()
    
    sys.exit(app.exec())
