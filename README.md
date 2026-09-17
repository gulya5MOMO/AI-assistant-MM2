# 🕊️ MM2 Trade AI Project

> **Ультимативный автономный ИИ-калькулятор окупаемости трейдов** для Roblox Murder Mystery 2.
> Работает **полностью локально** — без серверов, без подписок, без сбора данных. Твои трейды — только твои.

🌐 **Официальный сайт:** [mm2trade-ii-assistant.vercel.app](https://mm2trade-ii-assistant.vercel.app/)

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![Ollama](https://img.shields.io/badge/AI-Ollama%20llama3.2%3A3b-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)

---

## 📖 О проекте

**MM2 Trade AI Project** — это десктопный помощник для трейдеров в Roblox Murder Mystery 2. Софт локально поднимает нейросеть **Llama 3.2 (3B)** через Ollama и на основе твоей собственной базы цен из `mm2_prices.txt` считает, выгоден ли трейд.
---

## ✨ Возможности

- 🤖 **Локальный ИИ** — Llama 3.2 3B работает на твоём ПК, никаких внешних API
- 🧮 **Точный расчёт окупаемости** — считает по твоей базе цен из `mm2_prices.txt`
- 🔊 **Озвучка вердикта** — голосом сообщает результат трейда
- 🕊️ **Работа в трее** — сидит в скрытых значках рядом с часами, трей-меню по правой кнопке (Показать / Скрыть / Выйти)
- 💸 **Бесплатно навсегда** — никаких подписок, активаций и «премиум-версий»
---

## ⚠️ Важно знать

> ИИ может **ошибиться в цифрах ** — это нормально для локальной модели.
> Но сам факт он определит верно: **в плюсе ты или в минусе по трейду**.
> Для 100% точности всегда заполняй `mm2_prices.txt` актуальными ценами.

---

## 🚀 Быстрый старт

### Шаг 0. Установи Python

Скачай **Python 3.11 или 3.12** с официального сайта [python.org](https://python.org).

> ⚠️ **ОБЯЗАТЕЛЬНО** при установке поставь галочку **Add Python to PATH** — иначе консоль не поймёт команду `pip`.

### Шаг 1. Установи Ollama и скачай мозги ИИ

1. Скачай [Ollama](https://ollama.com) и запусти её.
2. Открой Командную строку Windows и выполни:

```bash
ollama run llama3.2:3b
```

Ждём, пока скачаются ~2 ГБ мозгов. Это делается один раз.

### Шаг 2. Установи библиотеки

Нажми `Win + R`, вбей `cmd`, нажми Enter. В чёрном терминале выполни:

```bash
pip install PyQt6 Pillow easyocr pyttsx3 requests pyinstaller
```

### Шаг 3. Запуск

1. Распакуй архив с проектом.
2. Зайди в папку `MM2_Trade_AI — Valera`, вытащи оттуда `pigeon.bat` (или его ярлык) на Рабочий стол.
3. Переименуй папку `MM2_Trade_AI — Valera` → `MM2_Trade_AI` (без приписок).
4. Запусти `pigeon.bat` — в трее появится иконка голубя 🕊️.

**Управление иконкой в трее:**
- 🖱️ **ЛКМ** — показать окно
- 🖱️ **ПКМ** — трей-меню: Показать / Скрыть / Выйти полностью

### Шаг 4. Настрой базу цен

Открой `mm2_prices.txt` и впиши свои цены в формате:

```
chroma_lightbringer = 3500
batwing = 1200
corrupt = 800
```

---

## 🌐 Полезные ссылки

- 🏠 **Сайт проекта:** [mm2trade-ii-assistant.vercel.app](https://mm2trade-ii-assistant.vercel.app/)
- 💬 **GitHub:** [github.com/gulya5MOMO](https://github.com/gulya5MOMO)

---

## 👤 Автор

**gulya5MOMO** — [github.com/gulya5MOMO](https://github.com/gulya5MOMO) 🕊️
