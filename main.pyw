import sys
import os
import re
import threading
import winreg
import traceback
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtGui import QColor, QIcon, QAction
from PIL import Image, ImageGrab


def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

ICON_PATH = resource_path("pigeon.png")


# ============ БАЗА ЦЕН ============
PRICES = {
    "gingerscope": 900, "evergreen": 300, "evergun": 280, "elderwood blade": 110,
    "chroma evergreen": 320, "chroma evergun": 310, "chroma gemstone": 38,
    "chroma boneblade": 30, "chroma tides": 35, "luger": 60, "heat": 50, "corrupt": 220,
    "chroma slasher": 40, "chroma laser": 45, "chroma gingerblade": 25, "chroma seer": 30
}

OCR_FIXES = {
    "slashcr": "chroma slasher", "lascr": "chroma laser", "secr": "chroma seer",
    "chmmok": "chroma", "cliroma": "chroma", "plater": "player",
    "xlo": "x10", "x1o": "x10"
}

# Глобальная ссылка на reader (грузится в фоне)
reader = None
ocr_ready = False


def load_ocr_background():
    """Грузит EasyOCR в фоне — 20-30 секунд."""
    global reader, ocr_ready
    try:
        print("[OCR] Загружаю EasyOCR...")
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        ocr_ready = True
        print("[OCR] ✅ Готово")
    except Exception as e:
        print(f"[OCR] ❌ Ошибка: {e}")
        traceback.print_exc()


# ============ ОЗВУЧКА ============
def say_voice(text):
    print(f"[Голос]: {text}")
    try:
        import pyttsx3
        eng = pyttsx3.init()
        eng.setProperty('rate', 165)
        eng.setProperty('volume', 1.0)
        ru_voice_id = None
        for v in eng.getProperty('voices'):
            name = (v.name or "").lower()
            vid = (v.id or "").lower()
            if ('ru' in vid) or ('russian' in name) or ('irina' in name) or ('pavel' in name):
                ru_voice_id = v.id
                break
        if ru_voice_id:
            eng.setProperty('voice', ru_voice_id)
        eng.say(text)
        eng.runAndWait()
        eng.stop()
    except Exception as e:
        print(f"Ошибка озвучки: {e}")


# ============ КНОПКА ============
class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._bg_color = QColor("#ff4757")
        self._update_style()

    def get_bg_color(self): return self._bg_color
    def set_bg_color(self, color):
        self._bg_color = color
        self._update_style()

    bgColor = pyqtProperty(QColor, fget=get_bg_color, fset=set_bg_color)

    def _update_style(self):
        c = self._bg_color.name()
        self.setStyleSheet(
            f"background-color: {c}; color: white; font-weight: bold; "
            f"font-size: 14px; border-radius: 10px; border: 2px solid #ffffff; padding: 10px;"
        )


class OverlayButton(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.drag_pos = None

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.btn = AnimatedButton("АНАЛИЗ ТРЕЙДА", self)
        self.btn.clicked.connect(self.on_click)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.btn)
        self.setLayout(layout)
        self.setGeometry(100, 100, 170, 60)

        self.anim_press = QPropertyAnimation(self.btn, b"bgColor", self)
        self.anim_press.setDuration(180)
        self.anim_press.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_release = QPropertyAnimation(self.btn, b"bgColor", self)
        self.anim_release.setDuration(200)
        self.anim_release.setEasingCurve(QEasingCurve.Type.OutCubic)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def on_click(self):
        self.anim_press.stop()
        self.anim_release.stop()
        self.anim_press.setStartValue(self.btn.get_bg_color())
        self.anim_press.setEndValue(QColor("#2ecc71"))
        self.anim_press.start()
        QTimer.singleShot(250, self._reset_color)
        threading.Thread(target=self.take_and_analyze, daemon=True).start()

    def _reset_color(self):
        self.anim_release.stop()
        self.anim_release.setStartValue(self.btn.get_bg_color())
        self.anim_release.setEndValue(QColor("#ff4757"))
        self.anim_release.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_pos is not None and (event.buttons() & Qt.MouseButton.RightButton):
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.drag_pos = None
            event.accept()

    def take_and_analyze(self):
        if not ocr_ready:
            print("[!] OCR ещё грузится, подожди 10-20 сек...")
            say_voice("Читалка ещё загружается, подожди немного.")
            return

        print("\n[1/3] Делаю скриншот...")
        screenshot_path = "trade_screenshot.png"
        try:
            img = ImageGrab.grab()
            img.save(screenshot_path)
        except Exception as e:
            print(f"Ошибка скриншота: {e}")
            return

        print("[2/3] Извлекаю текст...")
        try:
            ocr_result = reader.readtext(screenshot_path, detail=0, paragraph=True)
            raw_text = " ".join(ocr_result).lower()
            fixed_text = raw_text
            for mistake, correction in OCR_FIXES.items():
                fixed_text = fixed_text.replace(mistake, correction)
            print(f"Текст: {fixed_text}")
        except Exception as e:
            print(f"Ошибка OCR: {e}")
            return

        our_sum = 0
        their_sum = 0
        parts = fixed_text.split("their offer")
        our_text = parts[0] if len(parts) > 0 else ""
        their_text = parts[1] if len(parts) > 1 else fixed_text

        for item, price in PRICES.items():
            if item in our_text:
                count_match = re.search(r'x\s*(\d+)', our_text)
                count = int(count_match.group(1)) if count_match else 1
                if "heat" in item and ("25" in our_text or "zs" in our_text):
                    count = 25
                our_sum += price * count

        for item, price in PRICES.items():
            if item in their_text:
                count_match = re.search(r'x\s*(\d+)', their_text)
                count = int(count_match.group(1)) if count_match else 1
                their_sum += price * count

        print(f"[Математика] Наша: {our_sum}, Их: {their_sum}")

        if our_sum == 0 and their_sum == 0:
            final_phrase = "Не удалось распознать скины на экране. Попробуй еще раз."
        elif their_sum > our_sum:
            final_phrase = f"Это окуп на {their_sum - our_sum} валюты! Трейд выгодный, соглашайся."
        elif their_sum < our_sum:
            final_phrase = f"Это минус на {our_sum - their_sum} values! Трейд невыгодный, отклоняй."
        else:
            final_phrase = "Трейд абсолютно равный по стоимости."

        print(f"=== ВЕРДИКТ: {final_phrase} ===")
        say_voice(final_phrase)


# ============ ТРЕЙ ============
class TrayApp:
    def __init__(self, app, overlay):
        self.app = app
        self.overlay = overlay

        icon = QIcon(ICON_PATH) if os.path.exists(ICON_PATH) else QIcon()
        self.tray = QSystemTrayIcon(icon, app)
        self.tray.setToolTip("Pigeon Trade Checker 🕊️")

        menu = QMenu()
        act_toggle = QAction("Показать / Скрыть", self.app)
        act_toggle.triggered.connect(self.toggle_overlay)
        act_show = QAction("Показать кнопку", self.app)
        act_show.triggered.connect(self.show_overlay)
        act_hide = QAction("Скрыть кнопку", self.app)
        act_hide.triggered.connect(self.hide_overlay)
        menu.addAction(act_toggle)
        menu.addSeparator()
        menu.addAction(act_show)
        menu.addAction(act_hide)
        menu.addSeparator()
        act_exit = QAction("Выход (закрыть полностью)", self.app)
        act_exit.triggered.connect(self.quit_app)
        menu.addAction(act_exit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()
        print("[Tray] ✅ Иконка показана")

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_overlay()

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.show_overlay()

    def show_overlay(self):
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()

    def hide_overlay(self):
        self.overlay.hide()

    def quit_app(self):
        print("[i] Выход...")
        self.tray.hide()
        self.app.quit()


# ============ ЗАПУСК ============
if __name__ == "__main__":
    start_hidden = "--hidden" in sys.argv

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    # 1) СНАЧАЛА запускаем OCR в фоне (чтобы не тормозить запуск)
    threading.Thread(target=load_ocr_background, daemon=True).start()

    # 2) СРАЗУ показываем трей + оверлей
    overlay = OverlayButton()
    if not start_hidden:
        overlay.show()

    tray = TrayApp(app, overlay)

    print("[START] Приложение запущено. OCR грузится в фоне...")
    sys.exit(app.exec())
