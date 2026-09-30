import sys
import os
import re
import io
import json
import time
import asyncio
import ctypes
import threading
import pythoncom
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import (
    Qt, QPoint, QPropertyAnimation, QEasingCurve, QTimer,
    pyqtProperty, QObject, pyqtSignal, pyqtSlot
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QSystemTrayIcon, QMenu, QMessageBox, QDialog, QLabel
)
from PyQt6.QtGui import QColor, QIcon, QAction, QActionGroup
from PIL import Image, ImageGrab, ImageEnhance, ImageOps


try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Pigeon.Trade.Checker.1.0")
except:
    pass


# ============ СЛОВАРЬ АНГЛ → РУС ДЛЯ СКИНОВ MM2 ============
RU_NAMES = {
    "luger": "люгер", "red luger": "красный люгер", "green luger": "зелёный люгер",
    "blue luger": "синий люгер", "yellow luger": "жёлтый люгер", "orange luger": "оранжевый люгер",
    "chroma luger": "хрома люгер", "heat": "хит", "chroma heat": "хрома хит",
    "corrupt": "коррапт", "chroma corrupt": "хрома коррапт", "clockwork": "клокворк",
    "chroma clockwork": "хрома клокворк", "deathshard": "дешард", "chroma deathshard": "хрома дешард",
    "fang": "фанг", "chroma fang": "хрома фанг", "gemstone": "гемстоун",
    "chroma gemstone": "хрома гемстоун", "gingerblade": "джинджерблейд",
    "chroma gingerblade": "хрома джинджерблейд", "ginger luger": "джинджер люгер",
    "laser": "лазер", "chroma laser": "хрома лазер", "saw": "пила", "chroma saw": "хрома пила",
    "seer": "сир", "chroma seer": "хрома сир", "blue seer": "синий сир",
    "red seer": "красный сир", "purple seer": "фиолетовый сир",
    "orange seer": "оранжевый сир", "yellow seer": "жёлтый сир",
    "shark": "шарк", "chroma shark": "хрома шарк", "slasher": "слэшер",
    "chroma slasher": "хрома слэшер", "tides": "тайдс", "chroma tides": "хрома тайдс",
    "nightblade": "найтблейд", "ghostblade": "гостблейд", "amerilaser": "америлазер",
    "batwing": "батвинг", "icebreaker": "айсбрейкер", "cookieblade": "кукиблейд",
    "candy": "канди", "darkbringer": "даркбрингер", "chroma darkbringer": "хрома даркбрингер",
    "lightbringer": "лайтбрингер", "chroma lightbringer": "хрома лайтбрингер",
    "bioblade": "биоблейд", "chroma bioblade": "хрома биоблейд",
    "evergreen": "эвергрин", "chroma evergreen": "хрома эвергрин",
    "evergun": "эверган", "chroma evergun": "хрома эверган", "virtual": "виртуал",
    "traveler's gun": "пушка путешественника", "travelers gun": "пушка путешественника",
    "elderwood blade": "элдервуд клинок", "elderwood scythe": "элдервуд коса",
    "elderwood revolver": "элдервуд револьвер", "gingerscope": "джинджерскоп",
    "harvester": "харвестер", "icewing": "айсвинг", "icepiercer": "айспирсер",
    "swirly axe": "свирли топор", "swirly gun": "свирли пушка", "swirly blade": "свирли клинок",
    "hallowscythe": "халлоу коса", "logchopper": "логчоппер", "plasmite": "плазмит",
    "plasmabeam": "плазмабим", "plasmablade": "плазмаблейд", "flames": "пламя",
    "candleflame": "кандлфлейм", "chroma candleflame": "хрома кандлфлейм",
    "peppermint": "пепперминт", "snowflake": "снежинка", "eggblade": "эггблейд",
    "prismatic": "призматик", "frostbite": "фростбайт", "frostsaber": "фростсейбер",
    "pumpking": "пампкинг", "boneblade": "боунблейд", "chroma boneblade": "хрома боунблейд",
    "spider": "паук", "chill": "чилл", "xmas": "рождество", "eternal": "этернал",
    "eternal ii": "этернал 2", "eternal iii": "этернал 3", "eternal iv": "этернал 4",
    "eternalcane": "этерналкейн", "gingermint": "джинджерминт", "jinglegun": "джинглган",
    "lugercane": "люгеркейн", "minty": "минтy", "swirlyblade": "свирли клинок",
    "nebula": "небула", "pixel": "пиксель", "battleaxe": "боевой топор",
    "battleaxe ii": "боевой топор 2", "hallowgun": "халлоган", "icebeam": "айсбим",
    "iceflake": "айсфлейк", "blaster": "бластер", "old glory": "олд глори",
    "iceblaster": "айсбластер", "sugar": "шугар", "pearl": "перл",
    "pearlshine": "перлшайн", "heartblade": "хартблейд", "watergun": "водяной пистолет",
    "borealis": "бореалис", "australis": "австралис", "bat": "бат",
    "beachy": "бичи", "sands": "сандс", "snowcannon": "сновкэннон",
    "snowstorm": "сновшторм", "snow dagger": "снежный кинжал", "sweet": "свит",
    "treat": "трит", "icecream": "мороженое", "heart wand": "палочка сердца",
    "ornament": "орнамент", "blizzard": "близзард", "spirit": "спирит",
    "soul": "соул", "ocean": "океан", "waves": "волны", "flora": "флора",
    "bloom": "блюм", "flowerwood": "флауэрвуд", "flowerwood gun": "флауэрвуд пушка",
    "sunset": "закат", "sunrise": "восход", "rainbow": "радуга",
    "rainbow gun": "радужная пушка", "bauble": "баубл", "xenoknife": "ксенонож",
    "xenoshot": "ксенопушка", "sakura": "сакура", "blossom": "блоссом",
    "darkshot": "даркшот", "darksword": "дарксворд", "turkey": "индейка",
    "alienbeam": "алиенбим", "raygun": "рейган", "constellation": "созвездие",
    "vampire's gun": "пушка вампира", "vampire's edge": "клинок вампира",
    "vampire's axe": "топор вампира", "vampires gun": "пушка вампира",
    "vampires edge": "клинок вампира", "vampires axe": "топор вампира",
    "celestial": "селестиал", "chroma bauble": "хрома баубл",
    "chroma constellation": "хрома созвездие", "chroma sunrise": "хрома восход",
    "chroma sunset": "хрома закат", "chroma watergun": "хрома водяной пистолет",
    "chroma snow dagger": "хрома снежный кинжал", "chroma snowcannon": "хрома сновкэннон",
    "chroma snowstorm": "хрома сновшторм", "chroma sweet": "хрома свит",
    "chroma treat": "хрома трит", "chroma heart wand": "хрома палочка сердца",
    "chroma icecream": "хрома мороженое", "chroma sands": "хрома сандс",
    "chroma beachy": "хрома бичи", "chroma ornament": "хрома орнамент",
    "chroma blizzard": "хрома близзард", "chroma alienbeam": "хрома алиенбим",
    "chroma raygun": "хрома рейган", "chroma traveler's gun": "хрома пушка путешественника",
    "chroma travelers gun": "хрома пушка путешественника", "chroma vampire's gun": "хрома пушка вампира",
}


def resource_path(filename):
    """Файлы ЗАШИТЫЕ в .exe (иконка)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)


def project_dir():
    """
    Папка ГДЕ ЛЕЖИТ mm2_prices.txt — всегда MM2_Trade_Assistant.
    Если запущен .exe из dist/PigeonTradeAssistant/ — поднимаемся на 2 уровня вверх.
    Если запущен .py — просто папка с main.py.
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)              # .../dist/PigeonTradeAssistant
        project_root = os.path.dirname(os.path.dirname(exe_dir))  # .../MM2_Trade_Assistant
        if os.path.isdir(project_root):
            return project_root
        return exe_dir
    return os.path.dirname(os.path.abspath(__file__))


ICON_PATH = resource_path("pigeon.png")
PROJECT_DIR = project_dir()
PRICES_PATH = os.path.join(PROJECT_DIR, "mm2_prices.txt")
POSITION_PATH = os.path.join(PROJECT_DIR, "position.json")
SETTINGS_PATH = os.path.join(PROJECT_DIR, "settings.json")

print(f"[PATH] mm2_prices.txt: {PRICES_PATH}")


DEFAULT_POS = (100, 100)
DEFAULT_LANG = "ru"


# ============ НАСТРОЙКИ ============
def load_settings():
    defaults = {"voice_lang": DEFAULT_LANG}
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            defaults.update(data)
    except Exception as e:
        print(f"[SETTINGS] Ошибка чтения: {e}")
    return defaults


def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SETTINGS] Ошибка записи: {e}")


SETTINGS = load_settings()
print(f"[SETTINGS] Язык голоса: {SETTINGS.get('voice_lang', DEFAULT_LANG)}")


def load_position():
    try:
        if os.path.exists(POSITION_PATH):
            with open(POSITION_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            x = int(data.get("x", DEFAULT_POS[0]))
            y = int(data.get("y", DEFAULT_POS[1]))
            print(f"[POS] Загружена позиция: ({x}, {y})")
            return (x, y)
    except Exception as e:
        print(f"[POS] Ошибка загрузки: {e}")
    return DEFAULT_POS


def save_position(x, y):
    try:
        with open(POSITION_PATH, "w", encoding="utf-8") as f:
            json.dump({"x": int(x), "y": int(y)}, f)
    except Exception as e:
        print(f"[POS] Ошибка сохранения: {e}")


SKIP_WORDS = {
    "weapons", "pets", "misc", "knives", "guns", "search", "trade", "your",
    "offer", "their", "inventory", "shop", "spectate", "emotes", "join",
    "leave", "menu", "settings", "back", "next", "previous", "loading",
    "waiting", "please", "wait", "before", "accepting", "accepted", "other",
    "player", "has", "yes", "no", "ok", "cancel", "confirm", "decline",
    "accept", "sure", "are", "add", "remove", "value", "demand",
    "rarity", "stability", "range", "godly", "chroma", "ancient", "vintage",
    "unique", "rare", "uncommon", "common", "legendary", "collectible",
    "supremevalues", "com", "the", "and", "or", "a", "an", "of", "to", "in",
    "on", "is", "it", "at", "by", "for", "with", "you", "we",
    "nonck", "nouck", "noick", "nonk", "nock", "poick",
    "ilonck", "iionck", "lponck", "1onck",
    "youroff", "theiroff", "youroffer", "theiroffer", "otter", "otfer",
    "x", "q", "u",
    "ваш", "ваше", "ваша", "вашего", "вашу", "вашей",
    "их", "обмен", "предложение", "предложения", "предложению",
    "предлож", "предложен", "жду", "ожидание", "пожалуйста", "подожди",
    "принятия", "принять", "принято", "другой", "игрок", "принял",
    "уверены", "отмена", "отменить", "отклонить", "отказ", "отклонено",
    "оружие", "ножи", "пушки", "питомцы", "поиск", "найти",
    "торговля", "инвентарь", "магазин", "назад", "далее", "меню",
    "настройки", "выбрать", "сортировать", "просмотр", "создать",
    "главная", "галерея", "рабочий", "стол", "документы", "загрузки",
    "изображения", "видео", "музыка", "снимки", "экрана", "этот",
    "компьютер", "сеть", "диск", "сетевой", "корзина", "элемент",
    "элементов", "папка", "файл", "имя", "дата", "тип", "размер",
    "звук", "лупа", "обзор", "ярлык", "открыть", "закрыть",
    "предл", "запрос", "трейд", "скины", "вещи", "хром",
}

MM2V_CATEGORIES = {
    "ancient": "Ancient", "unique": "Unique", "chroma": "Chroma",
    "godly": "Godly", "legend": "Legendary", "rare": "Rare",
    "uncommon": "Uncommon", "common": "Common", "vintage": "Vintage",
    "pets": "Pet", "misc": "Misc",
}


def parse_price(price_str):
    if price_str is None:
        return None
    s = str(price_str).strip().replace(",", "").replace(" ", "").replace("$", "")
    multiplier = 1
    if s.endswith(('k', 'K', 'к', 'К')):
        multiplier = 1_000; s = s[:-1]
    elif s.endswith(('m', 'M', 'м', 'М')):
        multiplier = 1_000_000; s = s[:-1]
    elif s.endswith(('b', 'B', 'б', 'Б')):
        multiplier = 1_000_000_000; s = s[:-1]
    try:
        return int(float(s) * multiplier)
    except ValueError:
        return None


def load_local_prices():
    prices = {}
    if not os.path.exists(PRICES_PATH):
        return prices
    lines = None
    for enc in ['utf-8-sig', 'utf-8', 'cp1251', 'utf-16']:
        try:
            with open(PRICES_PATH, "r", encoding=enc) as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if not lines:
        return prices
    cats = {"chroma", "godly", "ancient", "vintage", "common", "uncommon",
            "rare", "legendary", "unique", "unknown", "set", "pet", "misc"}
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
        price = parse_price(parts[-1])
        if price is None:
            continue
        for part in parts[:-1]:
            name_clean = re.sub(r'[^\w\s]', '', part.lower(), flags=re.UNICODE).strip()
            if not name_clean or len(name_clean) < 3 or name_clean in cats:
                continue
            prices[name_clean] = price
    print(f"[LOCAL] Загружено {len(prices)} цен из {PRICES_PATH}")
    return prices


LOCAL_PRICES = load_local_prices()


# ============ БРАУЗЕР ============
_driver = None
_driver_lock = threading.Lock()
_web_lock = threading.Lock()   # 🔧 ФИКС #1: защита Chrome от параллельных driver.get()


def create_chrome():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--log-level=3")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--page-load-strategy=eager")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    try:
        driver.command_executor._client_config.timeout = 15
    except:
        pass
    try:
        driver.set_page_load_timeout(15)
        driver.set_script_timeout(15)
    except:
        pass
    return driver


def get_driver():
    global _driver
    with _driver_lock:
        # 🔧 ФИКС #2: проверяем, жив ли существующий драйвер
        if _driver is not None:
            try:
                _ = _driver.current_url  # лёгкий ping
                return _driver
            except Exception:
                print("[BROWSER] ⚠ Chrome умер, пересоздаю...")
                try:
                    _driver.quit()
                except:
                    pass
                _driver = None
        try:
            print("[BROWSER] Chrome...")
            _driver = create_chrome()
            print("[BROWSER] ✅ Chrome готов")
            return _driver
        except Exception as e:
            print(f"[BROWSER] ❌ {e}")
            return None


# ============ ЗАГРУЗКА ЦЕН ============
def _extract_supreme_json(html):
    match = re.search(
        r'<script[^>]*id="sv-all-values"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except:
        return {}


def _parse_supreme_data(data):
    prices = {}
    cat_map = {
        "godlies": "Godly", "chromas": "Chroma", "ancients": "Ancient",
        "vintages": "Vintage", "uniques": "Unique", "legendaries": "Legendary",
        "rares": "Rare", "uncommons": "Uncommon", "commons": "Common",
        "pets": "Pet", "misc": "Misc", "sets": "Set",
    }
    for key, info in data.items():
        if "|" not in key:
            continue
        category, name = key.split("|", 1)
        price = parse_price(info.get("value"))
        if price is None:
            continue
        prices[name.lower().strip()] = (cat_map.get(category, category.capitalize()), price)
    return prices


def _parse_mm2v_category(text, cat_label):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    prices = {}
    skip = ['navigation', 'home', 'play mm2', 'inventory calculator',
            'sort by', 'filter', 'display', 'login', 'mm2values',
            'hot items', 'values updated', 'welcome', 'working on',
            'tier', 'demand', 'range', 'rarity', 'stability', 'wiki',
            'thanks for coming', 'privacy policy', 'mfdubs',
            '©', 'page', 'advertisement']
    for i, line in enumerate(lines):
        if i + 1 >= len(lines):
            break
        name = line
        next_line = lines[i + 1]
        if not next_line.startswith("Value:"):
            continue
        if any(p in name.lower() for p in skip):
            continue
        if len(name) < 2 or len(name) > 45:
            continue
        if name.startswith('-‹') or name.startswith('©'):
            continue
        if not re.match(r"^[A-Za-z0-9][A-Za-z0-9\'\-\s\.\(\)\/&]+$", name):
            continue
        price_str = next_line.replace("Value:", "").strip()
        if "X (T" in price_str:
            continue
        price = parse_price(price_str)
        if price is None:
            continue
        prices[name.lower().strip()] = (cat_label, price)
    return prices


def download_prices_from_web(stop_flag=None):
    driver = get_driver()
    if driver is None:
        return False, 0, "Chrome не запустился", "skipped"

    def should_stop():
        return stop_flag and stop_flag[0]

    all_prices = {}
    supreme_status = "skipped"
    supreme_count = 0

    try:
        if not should_stop():
            print("\n[DOWNLOAD] ══════════════════════════════════════")
            print("[DOWNLOAD] Открываю supremevalues.com...")
            try:
                with _web_lock:   # 🔧 ФИКС #1: тот же лок, что и у search_price_online
                    driver.get("https://supremevalues.com/")
                time.sleep(4)
                for i in range(40):
                    if should_stop():
                        return False, 0, "Отменено", supreme_status
                    try:
                        driver.execute_script("window.scrollBy(0, 900);")
                    except:
                        break
                    time.sleep(0.08)
                time.sleep(1)
                html = driver.page_source
                supreme = _parse_supreme_data(_extract_supreme_json(html))
                supreme_count = len(supreme)
                if supreme_count > 0:
                    supreme_status = "ok"
                    all_prices.update(supreme)
                    print(f"[DOWNLOAD]  ✅ supremevalues.com — {supreme_count} предметов")
                else:
                    supreme_status = "empty"
                    print(f"[DOWNLOAD]  ⚠ supremevalues.com — 0 предметов (пусто)")
            except Exception as e:
                supreme_status = "blocked"
                print(f"[DOWNLOAD]  ❌ supremevalues.com не пустил: {str(e)[:80]}")
            print("[DOWNLOAD] ══════════════════════════════════════")

        print("\n[DOWNLOAD] Открываю mm2values.com...")
        for cat_key, cat_label in MM2V_CATEGORIES.items():
            if should_stop():
                return False, 0, "Отменено", supreme_status
            try:
                print(f"  [{cat_label}]...")
                with _web_lock:   # 🔧 ФИКС #1
                    driver.get(f"https://mm2values.com/?p={cat_key}")
                time.sleep(2.5)
                for i in range(30):
                    if should_stop():
                        return False, 0, "Отменено", supreme_status
                    try:
                        driver.execute_script("window.scrollBy(0, 800);")
                    except:
                        break
                    time.sleep(0.08)
                time.sleep(1)

                text = driver.execute_script("return document.body.innerText")
                cat_prices = _parse_mm2v_category(text, cat_label)
                new_count = 0
                for name, val in cat_prices.items():
                    if name not in all_prices:
                        all_prices[name] = val
                        new_count += 1
                print(f"    ✅ +{new_count} новых (всего: {len(all_prices)})")
            except Exception as e:
                print(f"    ❌ {cat_label}: {str(e)[:80]}")
                continue

        if should_stop():
            return False, 0, "Отменено", supreme_status

        if not all_prices:
            return False, 0, "Не удалось загрузить ни одной цены", supreme_status

        ru_added = 0
        for en_name, (cat, price) in list(all_prices.items()):
            if en_name in RU_NAMES:
                ru_name = RU_NAMES[en_name]
                if ru_name not in all_prices:
                    all_prices[ru_name] = (cat, price)
                    ru_added += 1
        if ru_added > 0:
            print(f"[DOWNLOAD] 🇷🇺 Добавлено русских названий: {ru_added}")

        file_content = []
        for name in sorted(all_prices.keys()):
            cat, price = all_prices[name]
            file_content.append(f"{name}\t{cat}\t{price}")

        text_to_save = "\n".join(file_content) + "\n"

        try:
            os.makedirs(os.path.dirname(PRICES_PATH), exist_ok=True)
            with open(PRICES_PATH, "w", encoding="utf-8") as f:
                f.write(text_to_save)
            print(f"[DOWNLOAD] 💾 Сохранено: {PRICES_PATH}")
        except Exception as e:
            return False, 0, f"Не смог сохранить: {e}", supreme_status

        print(f"\n[DOWNLOAD] ✅ ЗАГРУЗКА ЗАВЕРШЕНА! Всего: {len(all_prices)} предметов")
        return True, len(all_prices), "Успешно", supreme_status
    except Exception as e:
        return False, 0, str(e), supreme_status


def search_price_online(item_name):
    driver = get_driver()
    if driver is None:
        return None
    # 🔧 ФИКС #1: сериализуем доступ к Chrome между потоками
    with _web_lock:
        query = f"mm2 {item_name} value supreme"
        try:
            driver.get(f"https://www.bing.com/search?q={query.replace(' ', '+')}&setlang=en&cc=us")
            time.sleep(1.0)
            text = driver.execute_script("return document.body.innerText").lower().replace(",", "")
            prices = []
            for m in re.finditer(r'(\d+(?:\.\d+)?)\s*([kmb])\b', text):
                try:
                    n = float(m.group(1))
                    sfx = m.group(2)
                    if sfx == 'k':
                        n *= 1_000
                    elif sfx == 'm':
                        n *= 1_000_000
                    elif sfx == 'b':
                        n *= 1_000_000_000
                    if 1 <= n <= 100_000_000_000:
                        prices.append(int(n))
                except:
                    continue
            if prices:
                from collections import Counter
                return Counter(prices).most_common(1)[0][0]
        except:
            pass
    return None


def get_price(item_name):
    key = item_name.lower().strip()
    if key in LOCAL_PRICES:
        return LOCAL_PRICES[key]
    return search_price_online(item_name)


# ============ OCR (EN + RU) ============
def _get_ocr_engine(lang_code):
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.globalization import Language
    try:
        return OcrEngine.try_create_from_language(Language(lang_code))
    except:
        return None


async def _ocr_single_async(pil_image, lang_code):
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
    engine = _get_ocr_engine(lang_code)
    if engine is None:
        return []
    result = await engine.recognize_async(bitmap)
    words = []
    for line in result.lines:
        for word in line.words:
            r = word.bounding_rect
            words.append({'text': word.text, 'x': int(r.x), 'y': int(r.y),
                          'w': int(r.width), 'h': int(r.height)})
    return words


def _text_quality(text):
    if not text:
        return 0
    letters = sum(1 for c in text if c.isalpha())
    weird = sum(1 for c in text if not c.isalpha() and not c.isdigit() and c != ' ')
    cyr = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
    return letters * 2 - weird * 3 + cyr


def ocr_words(pil_image):
    all_words = []
    try:
        try:
            pythoncom.CoInitialize()
        except:
            pass
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            en_words = loop.run_until_complete(_ocr_single_async(pil_image, 'en-US'))
            ru_words = loop.run_until_complete(_ocr_single_async(pil_image, 'ru-RU'))
        finally:
            loop.close()

        merged = []
        used_ru = set()
        for ew in en_words:
            best_ru = None
            best_idx = -1
            for i, rw in enumerate(ru_words):
                if i in used_ru:
                    continue
                if abs(ew['x'] - rw['x']) < 40 and abs(ew['y'] - rw['y']) < 20:
                    best_ru = rw
                    best_idx = i
                    break
            if best_ru:
                used_ru.add(best_idx)
                if _text_quality(best_ru['text']) > _text_quality(ew['text']):
                    merged.append(best_ru)
                else:
                    merged.append(ew)
            else:
                merged.append(ew)
        for i, rw in enumerate(ru_words):
            if i not in used_ru:
                merged.append(rw)
        all_words = merged
    except:
        pass
    return all_words


def enhance(img):
    w, h = img.size
    big = img.resize((w * 5, h * 5), Image.LANCZOS)
    big = big.convert('L')
    big = ImageOps.autocontrast(big, cutoff=2)
    bw = big.point(lambda x: 255 if x > 190 else 0)
    return bw.convert('RGB')


def enhance_small(img):
    w, h = img.size
    big = img.resize((w * 3, h * 3), Image.LANCZOS)
    return ImageEnhance.Contrast(big).enhance(1.4)


CYR_TO_LAT = {
    'а': 'a', 'в': 'b', 'г': 'r', 'е': 'e', 'ё': 'e', 'з': '3', 'и': 'u', 'й': 'u',
    'к': 'k', 'л': 'n', 'м': 'm', 'н': 'h', 'о': 'o', 'п': 'n', 'р': 'p', 'с': 'c',
    'т': 't', 'у': 'y', 'х': 'x', 'ч': '4', 'ы': 'b', 'ь': 'b', 'э': 'e', 'ю': 'o', 'я': 'r',
}


def clean_word(s):
    return re.sub(r'[^\w\s]', '', s.lower(), flags=re.UNICODE).strip()


def fix_homoglyphs(text):
    return ''.join(CYR_TO_LAT.get(ch, ch) for ch in text)


OFFER_MARKERS = [
    "предложение", "предложения", "предложению",
    "предлож", "предложен", "предл",
    "обмен", "обмена", "обмену",
    "offer", "otfer", "otter", "ofier", "ofrer", "ofter", "offor",
]


def find_offer_headers(words):
    offers = []
    for w in words:
        raw = w['text'].lower()
        t_clean = clean_word(raw)
        t_fixed = clean_word(fix_homoglyphs(raw))
        for marker in OFFER_MARKERS:
            if marker in t_clean or marker in t_fixed:
                offers.append(w)
                break
    if len(offers) >= 2:
        offers.sort(key=lambda w: w['y'])
        return offers[0], offers[1]
    if len(offers) == 1:
        o = offers[0]
        max_y = max((w['y'] for w in words), default=1000)
        if o['y'] < max_y * 0.5:
            their = dict(o); their['y'] = o['y'] + 290
            return o, their
        else:
            your = dict(o); your['y'] = max(0, o['y'] - 290)
            return your, o
    YOUR_M = ["your", "vour", "ваше", "ваш", "ваша", "твое", "твоё", "мое", "моё"]
    THEIR_M = ["their", "thelr", "их", "соперник", "противник"]
    your_word = their_word = None
    for w in words:
        raw = w['text'].lower()
        tc = clean_word(raw)
        tf = clean_word(fix_homoglyphs(raw))
        if your_word is None:
            for m in YOUR_M:
                if m in tc or m in tf:
                    your_word = w
                    break
        if their_word is None:
            for m in THEIR_M:
                if m in tc or m in tf:
                    their_word = w
                    break
    if your_word and their_word:
        if your_word['y'] > their_word['y']:
            your_word, their_word = their_word, your_word
        return your_word, their_word
    return None, None


def is_likely_skin_name(text):
    if not text or len(text) < 3 or len(text) > 25:
        return False
    if text in SKIP_WORDS:
        return False
    if not re.match(r"^[a-zа-яё][a-zа-яё0-9\']*$", text, re.UNICODE):
        return False
    if re.match(r'^\d+$', text):
        return False
    return True


def parse_side(words, y_min, y_max, side_name="SIDE"):
    side_words = [w for w in words if y_min <= w['y'] <= y_max]
    if not side_words:
        return []

    side_words.sort(key=lambda w: (w['y'], w['x']))
    lines = []
    current = []
    cur_y = None
    for w in side_words:
        if cur_y is None or abs(w['y'] - cur_y) > 80:
            if current:
                lines.append(current)
            current = [w]
            cur_y = w['y']
        else:
            current.append(w)
            cur_y = (cur_y + w['y']) // 2
    if current:
        lines.append(current)

    found = []
    seen = set()

    for line in lines:
        line.sort(key=lambda w: (w['y'], w['x']))
        tokens = []
        for w in line:
            v1 = clean_word(w['text'])
            v2 = clean_word(fix_homoglyphs(w['text']))
            chosen = v1 if len(v1) >= len(v2) else v2
            if not chosen:
                continue
            for p in chosen.split():
                if p:
                    tokens.append({'text': p, 'x': w['x'], 'y': w['y']})

        if not tokens:
            continue

        i = 0
        while i < len(tokens):
            matched = False
            for phrase_len in [3, 2, 1]:
                if i + phrase_len > len(tokens):
                    continue
                phrase_tokens = tokens[i:i + phrase_len]
                phrase = ' '.join(t['text'] for t in phrase_tokens)
                if not all(is_likely_skin_name(t['text']) for t in phrase_tokens):
                    continue
                if phrase in seen:
                    i += phrase_len
                    matched = True
                    break

                last_x = phrase_tokens[-1]['x']
                last_y = phrase_tokens[-1]['y']
                count = 1
                for j in range(len(tokens)):
                    nxt = tokens[j]
                    if nxt['x'] < last_x - 50:
                        continue
                    if abs(nxt['y'] - last_y) > 80:
                        continue
                    m = re.match(r'^x(\d+)$', nxt['text'])
                    if m:
                        try:
                            n = int(m.group(1))
                            if 1 <= n <= 99:
                                count = n
                        except:
                            pass
                        break

                is_chroma = False
                if i > 0 and ('chrom' in tokens[i-1]['text'] or 'хром' in tokens[i-1]['text']):
                    is_chroma = True

                final_name = phrase
                if is_chroma and not phrase.startswith('chroma') and not phrase.startswith('хрома'):
                    final_name = f"chroma {phrase}"

                if len(final_name) < 3:
                    continue

                seen.add(final_name)
                found.append({'name': final_name, 'count': count})
                i += phrase_len
                matched = True
                break
            if not matched:
                i += 1
    return found


# ============ ОЗВУЧКА С ВЫБОРОМ ЯЗЫКА ============
def say_voice(text_ru, text_en=None):
    global SETTINGS
    lang = SETTINGS.get("voice_lang", DEFAULT_LANG)
    text = text_ru if lang == "ru" else (text_en or text_ru)

    print(f"[Голос/{lang}]: {text}")

    try:
        pythoncom.CoInitialize()
    except:
        pass
    try:
        import pyttsx3
        eng = pyttsx3.init(driverName='sapi5')
        eng.setProperty('rate', 165)
        eng.setProperty('volume', 1.0)

        target_voice = None
        for v in eng.getProperty('voices'):
            name = (v.name or "").lower()
            vid = (v.id or "").lower()

            if lang == "ru":
                if ('ru' in vid) or ('russian' in name) or ('irina' in name) or ('pavel' in name):
                    target_voice = v.id
                    break
            else:
                if ('zira' in name) or ('david' in name) or ('en-us' in vid) or ('english' in name):
                    target_voice = v.id
                    break

        if target_voice:
            eng.setProperty('voice', target_voice)

        eng.say(text)
        eng.runAndWait()
        eng.stop()
    except Exception as e:
        print(f"[Голос] Ошибка: {e}")


# 🔧 ФИКС #4: проверка русского OCR при старте
def check_ru_ocr_available():
    """Проверяет, установлен ли русский OCR в Windows."""
    try:
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.globalization import Language
        try:
            engine = OcrEngine.try_create_from_language(Language('ru-RU'))
            return engine is not None
        except Exception:
            return False
    except Exception:
        return False


# ============ КАСТОМНЫЙ ДИАЛОГ ЗАГРУЗКИ ============
class LoadingDialog(QDialog):
    def __init__(self, parent=None, on_cancel=None):
        super().__init__(parent)
        self.on_cancel = on_cancel
        self._skip_confirm = False

        self.setWindowTitle("⏳ Загрузка цен")
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowTitleHint
        )
        self.setModal(False)
        self.setMinimumWidth(420)

        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        layout = QVBoxLayout()
        title = QLabel("Идёт загрузка цен из интернета...")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: white;")
        layout.addWidget(title)

        hint1 = QLabel("Это может занять 1-2 минуты.")
        hint1.setStyleSheet("color: #cccccc; margin-top: 8px;")
        layout.addWidget(hint1)

        hint2 = QLabel("По завершению программа напишет об этом.")
        hint2.setStyleSheet("color: #cccccc; margin-top: 4px;")
        layout.addWidget(hint2)

        layout.addSpacing(10)
        self.setLayout(layout)

        self.setStyleSheet("QDialog { background-color: #2b2b2b; }")

    def force_close(self):
        self._skip_confirm = True
        self.close()

    def closeEvent(self, event):
        if self._skip_confirm:
            event.accept()
            return

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Остановить загрузку?")
        msg.setText("Загрузка остановится и не докачается.")
        msg.setInformativeText("Точно закрыть?")
        btn_yes = msg.addButton("ДА, остановить", QMessageBox.ButtonRole.YesRole)
        btn_no = msg.addButton("НЕТ, продолжить", QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(btn_no)
        msg.exec()

        if msg.clickedButton() == btn_yes:
            if self.on_cancel:
                try:
                    self.on_cancel()
                except:
                    pass
            event.accept()
        else:
            event.ignore()


# ============ КНОПКА ============
class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._bg_color = QColor("#ff4757")
        self._update_style()

    def get_bg_color(self):
        return self._bg_color

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
        self._busy = False   # 🔧 ФИКС #3: флаг занятости анализа
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

        self.setFixedSize(170, 60)

        self.btn = AnimatedButton("АНАЛИЗ ТРЕЙДА", self)
        self.btn.clicked.connect(self.on_click)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.btn)
        self.setLayout(layout)

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
        # 🔧 ФИКС #3: не запускаем второй анализ, пока первый не закончился
        if self._busy:
            print("[ANALYZE] ⏳ Предыдущий анализ ещё идёт, клик пропущен")
            return
        self._busy = True

        self.anim_press.stop()
        self.anim_release.stop()
        self.anim_press.setStartValue(self.btn.get_bg_color())
        self.anim_press.setEndValue(QColor("#2ecc71"))
        self.anim_press.start()
        QTimer.singleShot(250, self._reset_color)
        threading.Thread(target=self._run_analysis, daemon=True).start()

    # 🔧 ФИКС #3: обёртка, которая снимает флаг после завершения
    def _run_analysis(self):
        try:
            self.take_and_analyze()
        finally:
            self._busy = False

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
            t0 = time.time()
            print("\n[ANALYZE] Начинаю...")

            full = ImageGrab.grab()
            W, H = full.size
            scale = 5

            enhanced_small = enhance_small(full)
            words_big = ocr_words(enhanced_small)
            if not words_big:
                say_voice("Не получилось прочитать экран.", "Couldn't read the screen.")
                return
            for w in words_big:
                w['x'] = int(w['x'] / 3)
                w['y'] = int(w['y'] / 3)
                w['w'] = int(w['w'] / 3)
                w['h'] = int(w['h'] / 3)

            your, their = find_offer_headers(words_big)
            if not your or not their:
                say_voice("Не вижу окно трейда.", "I can't see the trade window.")
                return

            y_your = your['y']
            y_their = their['y']
            line_words = [w for w in words_big if abs(w['y'] - y_their) < 50]
            if line_words:
                x_left = max(0, min(w['x'] for w in line_words) - 20)
                x_right = min(W, max(w['x'] + w['w'] for w in line_words) + 50)
            else:
                x_left = 0
                x_right = W

            crop_our = full.crop((x_left, max(0, y_your - 10), x_right, y_their - 20))
            crop_their = full.crop((x_left, y_their + 40, x_right, min(H, y_their + 500)))

            words_our = ocr_words(enhance(crop_our))
            words_their = ocr_words(enhance(crop_their))
            for w in words_our:
                w['x'] = int(w['x'] / scale)
                w['y'] = int(w['y'] / scale)
            for w in words_their:
                w['x'] = int(w['x'] / scale)
                w['y'] = int(w['y'] / scale)

            our_items = parse_side(words_our, 0, crop_our.size[1], "НАШИ")
            their_items = parse_side(words_their, 0, crop_their.size[1], "ИХ")

            print(f"[ANALYZE] Наши: {our_items}")
            print(f"[ANALYZE] Их: {their_items}")

            all_items = [(it['name'], 'our') for it in our_items] + \
                        [(it['name'], 'their') for it in their_items]

            results = {}
            if all_items:
                with ThreadPoolExecutor(max_workers=4) as ex:
                    futures = {ex.submit(get_price, name): (name, side) for name, side in all_items}
                    for fut in as_completed(futures):
                        name, side = futures[fut]
                        try:
                            results[(name, side)] = fut.result()
                        except:
                            results[(name, side)] = None

            our_total = 0
            their_total = 0
            for it in our_items:
                p = results.get((it['name'], 'our'))
                if p:
                    our_total += p * it['count']
            for it in their_items:
                p = results.get((it['name'], 'their'))
                if p:
                    their_total += p * it['count']

            print(f"[RESULT] Наша: {our_total}, Их: {their_total}, время: {time.time()-t0:.1f}с")

            if not our_items and not their_items:
                final_ru = "Не распознал скины. Попробуй еще раз."
                final_en = "Couldn't recognize skins. Try again."
            elif our_total == 0 and their_total == 0:
                final_ru = "Не нашёл цены на скины. Попробуй еще раз."
                final_en = "Couldn't find prices. Try again."
            elif our_total == 0:
                final_ru = f"Не нашёл цены на твои скины. Их сторона стоит {their_total}."
                final_en = f"Couldn't find prices for your skins. Their side is {their_total}."
            elif their_total == 0:
                final_ru = f"Не нашёл цены на скины соперника. Ты отдаёшь на {our_total}."
                final_en = f"Couldn't find prices for their skins. You give {our_total}."
            else:
                diff = their_total - our_total
                if diff > 0:
                    final_ru = f"Мы в плюсе на {diff} валют! Трейд выгодный, соглашайся."
                    final_en = f"We are plus {diff} value! Trade is profitable, accept."
                elif diff < 0:
                    final_ru = f"Мы в минусе на {abs(diff)} валют! Трейд невыгодный, отклоняй."
                    final_en = f"We are minus {abs(diff)} value! Trade is bad, decline."
                else:
                    final_ru = "Трейд ровный."
                    final_en = "Trade is even."

            print(f"[VERDICT RU] {final_ru}")
            print(f"[VERDICT EN] {final_en}")
            say_voice(final_ru, final_en)

        except Exception as e:
            print(f"[ERR] {e}")


# ============ ТРЕЙ ============
class TrayApp(QObject):
    download_done = pyqtSignal(bool, int, str, str)

    def __init__(self, app, overlay):
        super().__init__()
        self.app = app
        self.overlay = overlay
        self.overlay_visible = True
        self.saved_pos = None

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

        lang_menu = menu.addMenu("🌐 Язык голоса")

        self.lang_group = QActionGroup(self.app)
        self.lang_group.setExclusive(True)

        current_lang = SETTINGS.get("voice_lang", DEFAULT_LANG)

        act_ru = QAction("🇷🇺 Русский", self.app)
        act_ru.setCheckable(True)
        act_ru.setChecked(current_lang == "ru")
        act_ru.triggered.connect(lambda: self.set_voice_lang("ru"))
        self.lang_group.addAction(act_ru)
        lang_menu.addAction(act_ru)

        act_en = QAction("🇬🇧 English", self.app)
        act_en.setCheckable(True)
        act_en.setChecked(current_lang == "en")
        act_en.triggered.connect(lambda: self.set_voice_lang("en"))
        self.lang_group.addAction(act_en)
        lang_menu.addAction(act_en)

        menu.addSeparator()

        act_reset = QAction("🎯 Сбросить положение кнопки", self.app)
        act_reset.triggered.connect(self.reset_position)
        menu.addAction(act_reset)

        menu.addSeparator()

        act_download = QAction("📥 Скачать цены из интернета", self.app)
        act_download.triggered.connect(self.on_download_prices)
        menu.addAction(act_download)

        menu.addSeparator()

        act_exit = QAction("Выйти (полностью)", self.app)
        act_exit.triggered.connect(self.quit_app)
        menu.addAction(act_exit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()
        self.loading_dlg = None
        self.downloading = False
        self.stop_flag = [False]

        self.download_done.connect(self._on_download_finished)

    def set_voice_lang(self, lang):
        global SETTINGS
        SETTINGS["voice_lang"] = lang
        save_settings(SETTINGS)
        print(f"[SETTINGS] Язык голоса изменён на: {lang}")

        if lang == "ru":
            say_voice("Русский язык выбран.", "Russian language selected.")
        else:
            say_voice("Английский язык выбран.", "English language selected.")

    def reset_position(self):
        try:
            self.overlay.move(DEFAULT_POS[0], DEFAULT_POS[1])
            save_position(DEFAULT_POS[0], DEFAULT_POS[1])
            self.saved_pos = QPoint(DEFAULT_POS[0], DEFAULT_POS[1])
            print(f"[POS] Сброс положения: {DEFAULT_POS}")
        except Exception as e:
            print(f"[POS] Ошибка сброса: {e}")

    def on_download_prices(self):
        if self.downloading:
            return

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("⚠ Скачать цены из интернета?")
        msg.setText("ВНИМАНИЕ!")
        msg.setInformativeText(
            "Все текущие цены в файле mm2_prices.txt будут ПОЛНОСТЬЮ УДАЛЕНЫ "
            "и заменены на свежие из интернета.\n\n"
            "⚠ Скачаются НЕ ВСЕ цены и названия.\n\n"
            "❌ Отмена — ничего не изменится.\n"
            "✅ ОК — удалить старые цены и скачать новые.\n\n"
            "⚠ Внимание: сайты могут временно заблокировать ваш IP "
            "если обновлять цены слишком часто.\n"
            "Рекомендуется не чаще 1 раза в неделю."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg.button(QMessageBox.StandardButton.Ok).setText("✅ Да, скачать")
        msg.button(QMessageBox.StandardButton.Cancel).setText("❌ Отмена")
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)

        if msg.exec() != QMessageBox.StandardButton.Ok:
            return

        try:
            if os.path.exists(PRICES_PATH):
                os.remove(PRICES_PATH)
        except:
            pass

        self.downloading = True
        self.stop_flag = [False]

        try:
            self.saved_pos = self.overlay.pos()
        except:
            self.saved_pos = None

        try:
            self.overlay.hide()
            self.overlay_visible = False
        except:
            pass

        self.loading_dlg = LoadingDialog(on_cancel=self._cancel_download)
        self.loading_dlg.show()

        threading.Thread(target=self._do_download, daemon=True).start()

    def _cancel_download(self):
        self.stop_flag[0] = True
        self.downloading = False

        try:
            if self.loading_dlg:
                self.loading_dlg.force_close()
                self.loading_dlg = None
        except:
            pass

        try:
            if self.saved_pos is not None:
                self.overlay.move(self.saved_pos)
            self.overlay.show()
            self.overlay.raise_()
            self.overlay_visible = True
        except:
            pass

    def _do_download(self):
        success, count, message, supreme_status = download_prices_from_web(self.stop_flag)
        self.download_done.emit(success, count, message, supreme_status)

    @pyqtSlot(bool, int, str, str)
    def _on_download_finished(self, success, count, message, supreme_status):
        if not self.downloading and message == "Отменено":
            return

        self.downloading = False

        try:
            if self.loading_dlg:
                self.loading_dlg.force_close()
                self.loading_dlg = None
        except:
            pass

        try:
            if self.saved_pos is not None:
                self.overlay.move(self.saved_pos)
            self.overlay.show()
            self.overlay.raise_()
            self.overlay_visible = True
        except:
            pass

        if message == "Отменено":
            return

        global LOCAL_PRICES
        if success:
            LOCAL_PRICES = load_local_prices()

        msg = QMessageBox()
        if success:
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("✅ Готово!")
            msg.setText("Загрузка цен завершена!")
            msg.setInformativeText(
                f"Загружено: {count} предметов.\n\n"
                f"✅ Добавлены некоторые предметы на русском.\n"
                f"⚠ Скачалось не всё."
            )
        else:
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("❌ Ошибка")
            msg.setText("Не удалось скачать цены")
            msg.setInformativeText(f"{message}")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_overlay()

    def toggle_overlay(self):
        if self.downloading:
            return
        if self.overlay_visible:
            self.saved_pos = self.overlay.pos()
            self.overlay.hide()
            self.overlay_visible = False
        else:
            if self.saved_pos is not None:
                self.overlay.move(self.saved_pos)
            self.overlay.show()
            self.overlay.raise_()
            self.overlay.activateWindow()
            self.overlay_visible = True

    def show_overlay(self):
        if self.downloading:
            return
        if self.saved_pos is not None:
            self.overlay.move(self.saved_pos)
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()
        self.overlay_visible = True

    def hide_overlay(self):
        self.saved_pos = self.overlay.pos()
        self.overlay.hide()
        self.overlay_visible = False

    def quit_app(self):
        try:
            pos = self.overlay.pos()
            save_position(pos.x(), pos.y())
        except:
            pass

        def kill_chrome():
            global _driver
            try:
                if _driver:
                    _driver.quit()
            except:
                pass
            _driver = None

        threading.Thread(target=kill_chrome, daemon=True).start()

        try:
            self.tray.hide()
        except:
            pass

        self.app.quit()
        os._exit(0)


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

    threading.Thread(target=get_driver, daemon=True).start()

    saved_pos = load_position()

    overlay = OverlayButton()
    overlay.move(saved_pos[0], saved_pos[1])
    if not start_hidden:
        overlay.show()
    tray = TrayApp(app, overlay)

    # 🔧 ФИКС #4: проверка русского OCR (уведомление в трее, если нет)
    if not check_ru_ocr_available():
        print("[OCR] ⚠ Русский OCR не установлен в Windows.")
        try:
            tray.tray.showMessage(
                "Pigeon Trade Checker",
                "Русский OCR не установлен в Windows.\n"
                "Русские названия скинов могут не распознаваться.\n\n"
                "Параметры → Время и язык → Язык → Русский → Параметры → Оптическое распознавание",
                QSystemTrayIcon.MessageIcon.Warning,
                10000
            )
        except Exception as e:
            print(f"[OCR] Не смог показать уведомление: {e}")
    else:
        print("[OCR] ✅ Русский OCR доступен")

    sys.exit(app.exec())
