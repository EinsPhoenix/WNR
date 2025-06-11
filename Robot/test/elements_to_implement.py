import sys

from PySide6.QtWidgets import (
    QApplication,
    QDial,
    QMainWindow,
    QProgressBar,
    QSlider,
    QVBoxLayout,
    QWidget,
    QAbstractSlider,
    QColorDialog,
    QColormap,
    QGesture,
    QProgressDialog,
    QRubberBand
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Widgets App")

        layout = QVBoxLayout()
        widgets = [
            QDial,
            QProgressBar,
            QSlider,
            QAbstractSlider,
            QColorDialog,
            QProgressDialog
        ]

        for widget in widgets:
            layout.addWidget(widget())

        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()