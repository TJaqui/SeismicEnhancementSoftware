from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import sys
from app import App
import os
import traceback

# Necesario para evitar conflictos con librerías como OpenMP
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Crear un log de consola incluso en modo --noconsole
log_path = os.path.join(os.path.dirname(__file__), "output.log")
sys.stdout = open(log_path, "a", encoding="utf-8")  # "a" para acumular, o "w" para sobrescribir
sys.stderr = sys.stdout  # Captura también los errores

# Capturar errores no manejados
def log_uncaught_exceptions(ex_cls, ex, tb):
    print("\n⚠️ Uncaught Exception:")
    traceback.print_exception(ex_cls, ex, tb)

sys.excepthook = log_uncaught_exceptions

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())

