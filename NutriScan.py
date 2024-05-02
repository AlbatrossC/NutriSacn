import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QTextEdit, QVBoxLayout, QWidget, QScrollArea, QSizePolicy
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pytesseract as tess
from PIL import Image
import openai
from dotenv import load_dotenv
import os

load_dotenv()

class WorkerThread(QThread):
    image_processed = pyqtSignal(str)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        img = Image.open(self.image_path)
        gray_img = img.convert('L')
        text = tess.image_to_string(gray_img)

        task1 = '''I will provide you a text.
        The text is a list of ingredients scanned from an Image.
        Your Task is to filter out ingredients only from the list.
        And also mention any Consuming product or subproduct in it.'''

        messages_task1 = [
            {"role": "system", "content": task1},
            {"role": "user", "content": text}
        ]

        chat_task1 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages_task1,
            max_tokens=300,
            temperature=0.5,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        response_ingredients = chat_task1.choices[0].message.content.strip()

        task2 = """Analyse the product. provide each content in a new line. 
        Analyzing your product: [product name],
         - [List of ingredients].
        Common names of ingredients: [Common names of each ingredient] ,Function of ingredients: After listing the common names, briefly explain the function of each ingredient. For example, "sugar (sweetener)," "salt (flavor enhancer)," "cornstarch (thickener)," etc. 
        Dietary considerations: Provide any allergens (soy, wheat, peanuts, etc.) or other dietary restrictions (gluten-free, vegan, etc.) based on the ingredients. 
        Nutrient content: While a full nutritional breakdown might be beyond the scope, you can mention key nutrients like Vitamin C, fiber, or protein content based on the ingredients. (in numericals if possible)
        Sugar content: Highlight the amount of added sugar (if any) as this can be a concern for many consumers. 
        Intake of the product: [Based on the ingredients, suggest a recommended serving size or frequency of consumption]. This will depend on the product type and its overall nutritional profile. (suggest a recommended serving product per day / week / month)
        Safety assessment: [Whether the product is safe to consume or not] Phrased cautiously, mentioning if there are any ingredients that might be a concern for certain individuals (e.g., lactose intolerance for dairy products )
        Safety Ratings: [Answer it in a scale of 1-10] 1 being the least safe and 10 being the most safe"""

        messages_task2 = [
            {"role": "system", "content": task2},
            {"role": "user", "content": response_ingredients}
        ]

        chat_task2 = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages_task2,
        max_tokens=700,
        temperature=0.5,
        api_key=os.getenv("OPENAI_API_KEY"),
)


        response2 = chat_task2.choices[0].message.content.strip()
        self.image_processed.emit(response2)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Uploader")
        self.setGeometry(0, 0, 390, 844)  # iPhone 14 dimensions (1170x2532 / 3)
        self.setFixedSize(390, 844)  # Fix window size

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        # Add logo
        self.logo_label = QLabel(self)
        pixmap = QPixmap("logo.png").scaledToWidth(150)  # Adjust logo size
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)

        self.upload_button = QPushButton("Upload Image", self)
        self.upload_button.setStyleSheet("background-color: green; color: white;")
        self.upload_button.clicked.connect(self.open_file_dialog)
        self.upload_button.setFixedSize(200, 50)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(300, 300)

        self.text_box = QTextEdit(self)
        self.text_box.setFontPointSize(12)  # Set font size to 12
        self.text_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)  # Set size policy

        self.main_layout.addWidget(self.logo_label, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.upload_button, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.text_box)

        # Set Tesseract path
        tess.pytesseract.tesseract_cmd = r'C:/Users/Soham/AppData/Local/Programs/Tesseract-OCR/tesseract.exe'

    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)", options=options)
        if file_name:
            self.display_image(file_name)
            self.process_image(file_name)

    def display_image(self, file_path):
        pixmap = QPixmap(file_path)
        pixmap = pixmap.scaledToWidth(300)  # Scale image to fit label width
        self.image_label.setPixmap(pixmap)

    def process_image(self, image_path):
        self.worker_thread = WorkerThread(image_path)
        self.worker_thread.image_processed.connect(self.update_text_box)
        self.worker_thread.start()

    def update_text_box(self, text):
        self.text_box.setPlainText(text)

    def resizeEvent(self, event):
        self.adjust_widgets_size()

    def adjust_widgets_size(self):
        label_width = min(self.width() - 40, 300)  # Limit label width to 300
        button_width = min(self.width() - 40, 200)  # Limit button width to 200
        text_box_width = min(self.width() - 40, 380)  # Limit text box width to 380
        self.image_label.setFixedWidth(label_width)
        self.upload_button.setFixedWidth(button_width)
        self.text_box.setFixedWidth(text_box_width)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(window)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Enable vertical scrolling
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrolling
    scroll_area.show()
    sys.exit(app.exec_())
