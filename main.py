from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import sys
from app import App
import os 
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
