from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import sys
from app import App
import os
import traceback

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

log_path = os.path.join(os.path.dirname(__file__), "output.log")
sys.stdout = open(log_path, "a", encoding="utf-8")  # "a" para acumular, o "w" para sobrescribir
sys.stderr = sys.stdout  # Captura también los errores

def log_uncaught_exceptions(ex_cls, ex, tb):
    print("\n⚠️ Uncaught Exception:")
    traceback.print_exception(ex_cls, ex, tb)

sys.excepthook = log_uncaught_exceptions

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())

