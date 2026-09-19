import sys
import os
import re
import io
import asyncio
import threading
import difflib
import pythoncom
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtGui import QColor, QIcon, QAction
from PIL import Image, ImageGrab, ImageEnhance


def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)


def base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


ICON_PATH = resource_path("pigeon.png")
PRICES_PATH = os.path.join(base_dir(), "mm2_prices.txt")


def log(msg):
    pass  # логирование отключено


DEFAULT_PRICES = {
    "gingerscope": 900, "evergreen": 300, "evergun": 280, "elderwood blade": 110,
    "chroma evergreen": 320, "chroma evergun": 310, "chroma gemstone": 38,
    "chroma boneblade": 30, "chroma tides": 35, "luger": 60, "heat": 50, "corrupt": 220,
    "chroma slasher": 40, "chroma laser": 45, "chroma gingerblade": 25, "chroma seer": 30
}


def load_prices():
    if not os.path.exists(PRICES_PATH):
        return dict(DEFAULT_PRICES)
    prices = {}
    lines = None
    for enc in ['utf-8-sig', 'utf-8', 'cp1251', 'utf-16']:
        try:
            with open(PRICES_PATH, "r", encoding=enc) as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if lines is None:
        return dict(DEFAULT_PRICES)
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
        else:
            parts = [p.strip() for p in re.split(r"\s{2,}", line) if p.strip()]
        if len(parts) < 2:
            continue
        name = parts[0].lower().strip()
        price_str = parts[-1].replace(",", "").replace(" ", "").replace("$", "")
        try:
            price = int(float(price_str))
        except ValueError:
            continue
        prices[name] = price
    return prices if prices else dict(DEFAULT_PRICES)


PRICES = load_prices()
KNOWN_ITEMS = sorted(PRICES.keys(), key=lambda x: -len(x))

CHROMA_ITEMS = set()
for name in PRICES:
    if name.startswith("chroma "):
        CHROMA_ITEMS.add(name[len("chroma "):])


def fuzzy_find_item(word, cutoff=0.6):
    if not word or len(word) < 3:
        return None
    word = word.lower().strip()
    if word in PRICES:
        return word
    matches = difflib.get_close_matches(word, KNOWN_ITEMS, n=1, cutoff=cutoff)
    return matches[0] if matches else None


# ============ WINDOWS OCR ============
def _get_ocr_engine():
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.globalization import Language
    for lang_code in ['en', 'ru']:
        try:
            engine = OcrEngine.try_create_from_language(Language(lang_code))
            if engine:
                return engine
        except:
            continue
    try:
        return OcrEngine.try_create_from_user_profile_languages()
    except:
        return None


async def _ocr_words_async(pil_image):
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

    buf = io.BytesIO()
    pil_image.save(buf, format='PNG')
    data = buf.getvalue()

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream.get_output_stream_at(0))
    writer.write_bytes(data)
    await writer.store_async()
    await writer.flush_async()
    stream.seek(0)

    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()

    engine = _get_ocr_engine()
    if engine is None:
        return []

    result = await engine.recognize_async(bitmap)
    words = []
    for line in result.lines:
        for word in line.words:
            r = word.bounding_rect
            words.append({
                'text': word.text,
                'x': int(r.x), 'y': int(r.y),
                'w': int(r.width), 'h': int(r.height),
            })
    return words


def ocr_words(pil_image):
    result = []
    try:
        try:
            pythoncom.CoInitialize()
        except:
            pass
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_ocr_words_async(pil_image))
        finally:
            loop.close()
    except:
        pass
    return result


def enhance(img):
    w, h = img.size
    big = img.resize((w * 3, h * 3), Image.LANCZOS)
    big = ImageEnhance.Contrast(big).enhance(1.4)
    return big


def clean_word(s):
    return re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()


def find_offer_y(words):
    offers = []
    for w in words:
        t = clean_word(w['text'])
        if 'offer' in t or 'otfer' in t or 'otter' in t or t == 'offer':
            offers.append(w)
    return offers


# ============ ПАРСЕР ============
def parse_side(words, y_min, y_max, side_name):
    side_words = [w for w in words if y_min <= w['y'] <= y_max]
    side_words.sort(key=lambda w: (w['y'] // 30, w['x']))

    tokens = []
    for w in side_words:
        t = clean_word(w['text'])
        if not t:
            continue
        for p in t.split():
            if p:
                tokens.append({'text': p, 'y': w['y']})

    found = []
    used = set()

    for i, tok in enumerate(tokens):
        text = tok['text']

        if text in ("x", "your", "offer", "their", "chroma", "the", "and", "or",
                    "wait", "please", "before", "accepting", "other", "player",
                    "has", "accepted", "are", "you", "sure", "decline", "otfer", "otter"):
            continue
        if re.match(r'^x\d+$', text) or re.match(r'^\d+$', text):
            continue

        matched_item = None
        for item in KNOWN_ITEMS:
            if item in text:
                matched_item = item
                break
        if not matched_item:
            matched_item = fuzzy_find_item(text, cutoff=0.6)
        if not matched_item:
            continue

        is_chroma = False
        for j in range(max(0, i - 5), i):
            if abs(tokens[j]['y'] - tok['y']) < 120 and 'chrom' in tokens[j]['text']:
                is_chroma = True
                break

        count = 1
        for j in range(i + 1, min(len(tokens), i + 6)):
            if abs(tokens[j]['y'] - tok['y']) > 40:
                break
            m = re.match(r'^x(\d+)$', tokens[j]['text'])
            if m:
                try:
                    n = int(m.group(1))
                    if 1 <= n <= 999:
                        count = n
                except:
                    pass
                break

        final_name = matched_item
        if is_chroma and matched_item in CHROMA_ITEMS:
            final_name = f"chroma {matched_item}"
        if final_name not in PRICES:
            final_name = matched_item

        price = PRICES.get(final_name, 0)
        if price == 0:
            continue

        key = (final_name, tok['y'] // 30)
        if key in used:
            continue
        used.add(key)

        found.append({'name': final_name, 'count': count, 'price': price, 'total': price * count})

    return found


# ============ ОЗВУЧКА ============
def say_voice(text):
    try:
        pythoncom.CoInitialize()
    except:
        pass
    try:
        import pyttsx3
        eng = pyttsx3.init(driverName='sapi5')
        eng.setProperty('rate', 165)
        eng.setProperty('volume', 1.0)
        for v in eng.getProperty('voices'):
            name = (v.name or "").lower()
            vid = (v.id or "").lower()
            if ('ru' in vid) or ('russian' in name) or ('irina' in name) or ('pavel' in name):
                eng.setProperty('voice', v.id)
                break
        eng.say(text)
        eng.runAndWait()
        eng.stop()
    except:
        pass


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
        try:
            full = ImageGrab.grab()
            W, H = full.size

            enhanced = enhance(full)
            scale = 3

            words_big = ocr_words(enhanced)
            if not words_big:
                say_voice("Не получилось прочитать экран.")
                return

            for w in words_big:
                w['x'] //= scale
                w['y'] //= scale
                w['w'] //= scale
                w['h'] //= scale

            offers = find_offer_y(words_big)

            if len(offers) < 2:
                if len(offers) == 1:
                    y_your = offers[0]['y']
                    y_their = y_your + 200
                else:
                    say_voice("Не вижу окно трейда. Проверь что трейд открыт на экране.")
                    return
            else:
                offers.sort(key=lambda w: w['y'])
                y_your = offers[0]['y']
                y_their = offers[1]['y']

            line_words = [w for w in words_big if abs(w['y'] - y_their) < 50]
            if line_words:
                x_left = max(0, min(w['x'] for w in line_words) - 20)
                x_right = min(W, max(w['x'] + w['w'] for w in line_words) + 50)
            else:
                x_left = 0
                x_right = W

            y1_our = max(0, y_your - 10)
            y2_our = y_their - 20
            y1_their = y_their + 40
            y2_their = min(H, y_their + 500)

            crop_our = full.crop((x_left, y1_our, x_right, y2_our))
            crop_their = full.crop((x_left, y1_their, x_right, y2_their))

            words_our = ocr_words(enhance(crop_our))
            words_their = ocr_words(enhance(crop_their))

            for w in words_our:
                w['x'] //= scale
                w['y'] //= scale
            for w in words_their:
                w['x'] //= scale
                w['y'] //= scale

            our_found = parse_side(words_our, 0, crop_our.size[1], "НАШИ")
            their_found = parse_side(words_their, 0, crop_their.size[1], "ИХ")

            our_sum = sum(x['total'] for x in our_found)
            their_sum = sum(x['total'] for x in their_found)

            if not our_found and not their_found:
                final_phrase = "Не распознал скины. Попробуй еще раз."
            elif not our_found:
                final_phrase = "Не распознал твои скины. Попробуй еще раз."
            elif not their_found:
                final_phrase = "Не распознал скины соперника. Попробуй еще раз."
            else:
                diff = their_sum - our_sum
                if diff > 0:
                    final_phrase = f"Мы в плюсе на {diff} валют! Трейд выгодный, соглашайся."
                elif diff < 0:
                    final_phrase = f"Мы в минусе на {abs(diff)} валют! Трейд невыгодный, отклоняй."
                else:
                    final_phrase = "Трейд ровный."

            say_voice(final_phrase)
        except:
            pass


# ============ ТРЕЙ ============
class TrayApp:
    def __init__(self, app, overlay):
        self.app = app
        self.overlay = overlay

        icon = QIcon(ICON_PATH) if os.path.exists(ICON_PATH) else QIcon()
        self.tray = QSystemTrayIcon(icon, app)
        self.tray.setToolTip("Pigeon Trade Checker 🕊️")

        menu = QMenu()
        for text, slot in [("Показать / Скрыть", self.toggle_overlay),
                           ("Показать кнопку", self.show_overlay),
                           ("Скрыть кнопку", self.hide_overlay)]:
            a = QAction(text, self.app)
            a.triggered.connect(slot)
            menu.addAction(a)
        menu.addSeparator()
        act_exit = QAction("Выход (закрыть полностью)", self.app)
        act_exit.triggered.connect(self.quit_app)
        menu.addAction(act_exit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()

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
        self.tray.hide()
        self.app.quit()


# ============ ЗАПУСК ============
if __name__ == "__main__":
    try:
        pythoncom.CoInitialize()
    except:
        pass

    start_hidden = "--hidden" in sys.argv

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    overlay = OverlayButton()
    if not start_hidden:
        overlay.show()

    tray = TrayApp(app, overlay)

    sys.exit(app.exec())
