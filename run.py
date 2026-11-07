import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication

from app.core.constants import APP_NAME
from app.core.paths import resource_path
from app.ui.main_window import MainWindow


def _set_windows_app_id():
    """Faz a barra de tarefas do Windows mostrar o ícone do LHyper, não o do Python."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LHyper.Desktop")
    except Exception:  # noqa: BLE001 - puramente cosmético
        pass


def main():
    _set_windows_app_id()
    # Escala fracionária nítida em monitores com 125%/150% no Windows.
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(resource_path("assets/icons/favicon.ico")))
    app.setStyle("Fusion")  # base neutra e consistente para o QSS

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
