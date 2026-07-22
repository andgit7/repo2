#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Единый скрипт для парсинга и мониторинга поездов
ТОЧНАЯ КОПИЯ логики: scrab.py + workv2.sh + ex6.sh + tgbot_scrn.sh
"""

import os
import sys
import re
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests


# ============================================================================
# НАСТРОЙКИ - ИЗМЕНЯЙТЕ ЗДЕСЬ ВСЕ ПАРАМЕТРЫ
# ============================================================================

class Config:
    """Класс со всеми настройками скрипта"""
    
    # -------------------- ОСНОВНЫЕ НАСТРОЙКИ --------------------
    TRAIN_NUMBER = "018М"  # Номер поезда
    URL = "https://grandtrain.ru/search/2000000-2078001/30.09.2026/"
    WAIT_TIME = 30
    
    # -------------------- ПУТИ К ФАЙЛАМ --------------------
    BASE_DIR = "/home/and/te/snapshot"
    INPUT_FILE = "parsed_page.html"
    OUTPUT_FILE = "train.html"
    RESULT_FILE = "result.txt"
    SNAPSHOT_FILE = "grand_snapshot.txt"
    DIFF_FILE = "diff.txt"
    SCREENSHOT_FILE = "screenshot.png"
    LOG_FILE = "monitor.log"
    
    # -------------------- TELEGRAM --------------------
    TELEGRAM_TOKEN = "7840513805:AAESfH3LIHUn_50fC5NxclX2d9mvoYJxgpw"
    TELEGRAM_CHAT_ID = "376050665"
    SEND_SCREENSHOT = True
    SEND_MESSAGE = True
    
    # -------------------- НАСТРОЙКИ ПАРСИНГА --------------------
    ENCODING = 'utf-8'
    MIN_HTML_SIZE = 10000
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    STEP_DELAY = 1
    
    # -------------------- НАСТРОЙКИ БРАУЗЕРА И СКРИНШОТА --------------------
    HEADLESS = True
    WINDOW_WIDTH = 1000   # Ширина окна браузера
    WINDOW_HEIGHT = 1200  # Высота окна браузера
    
    # Масштаб страницы для скриншота (1.0 = 100%, 2.0 = 200% и т.д.)
    # Больше масштаб = более детальный скриншот, но может обрезаться
    SCREENSHOT_SCALE = 1.5  # Увеличение в 2 раза для лучшей детализации
    
    # Качество скриншота (только для PNG)
    SCREENSHOT_QUALITY = 100  # 1-100, где 100 - лучшее качество
    
    @classmethod
    def get_paths(cls):
        base = Path(cls.BASE_DIR)
        return {
            'base_dir': base,
            'parsed_html': base / cls.INPUT_FILE,
            'train_html': base / cls.OUTPUT_FILE,
            'result_file': base / cls.RESULT_FILE,
            'snapshot_file': base / cls.SNAPSHOT_FILE,
            'diff_file': base / cls.DIFF_FILE,
            'screenshot_file': base / cls.SCREENSHOT_FILE,
            'log_file': base / cls.LOG_FILE,
        }

# ============================================================================
# КОНЕЦ НАСТРОЕК
# ============================================================================


class TrainMonitor:
    """Класс для мониторинга поездов"""
    
    def __init__(self):
        self.config = Config
        self.paths = Config.get_paths()
        self.train_number = Config.TRAIN_NUMBER
        self.url = Config.URL
        self.wait_time = Config.WAIT_TIME
        self.encoding = Config.ENCODING
        
        # Настройки скриншота
        self.screenshot_scale = Config.SCREENSHOT_SCALE
        self.window_width = Config.WINDOW_WIDTH
        self.window_height = Config.WINDOW_HEIGHT
        
        self.paths['base_dir'].mkdir(parents=True, exist_ok=True)
        self.setup_logging()
        self.driver = None
        
        self.logger.info(f"🚂 Мониторинг поезда {self.train_number}")
        self.logger.info(f"📁 Рабочая директория: {self.paths['base_dir']}")
        self.logger.info(f"📸 Масштаб скриншота: {self.screenshot_scale}x")
    
    def setup_logging(self):
        """Настройка логирования"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        handlers = [logging.StreamHandler()]
        log_file = self.paths['log_file']
        handlers.append(logging.FileHandler(log_file, encoding=self.encoding))
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Настройка драйвера Chrome"""
        options = Options()
        
        if Config.HEADLESS:
            options.add_argument("--headless=new")
        
        # Устанавливаем размер окна с учётом масштаба
        # Для лучшего качества скриншота увеличиваем размер окна
        scaled_width = int(self.window_width * self.screenshot_scale)
        scaled_height = int(self.window_height * self.screenshot_scale)
        
        options.add_argument(f"--window-size={scaled_width},{scaled_height}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Устанавливаем масштаб страницы через JavaScript
            # Это увеличивает содержимое, делая скриншот более детальным
            if self.screenshot_scale != 1.0:
                self.driver.execute_script(f"document.body.style.zoom = '{self.screenshot_scale}'")
                self.logger.info(f"🔍 Установлен масштаб страницы: {self.screenshot_scale}x")
            
            self.logger.info(f"✅ Драйвер создан (окно: {scaled_width}x{scaled_height})")
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания драйвера: {e}")
            return False
    
    # ================================================================
    # ШАГ 1: Парсинг страницы - ТОЧНО КАК В scrab.py
    # ================================================================
    def parse_page(self) -> bool:
        """Парсинг страницы - как в scrab.py"""
        self.logger.info(f"📡 Загрузка: {self.url}")
        
        for attempt in range(Config.MAX_RETRIES):
            try:
                if not self.driver and not self.setup_driver():
                    continue
                
                self.driver.get(self.url)
                WebDriverWait(self.driver, self.wait_time).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                time.sleep(3)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                html_content = self.driver.page_source
                with open(self.paths['parsed_html'], 'w', encoding=self.encoding) as f:
                    f.write(html_content)
                
                file_size = os.path.getsize(self.paths['parsed_html'])
                self.logger.info(f"💾 HTML сохранён, размер: {file_size:,} байт")
                
                if file_size < Config.MIN_HTML_SIZE:
                    self.logger.warning(f"⚠️ HTML слишком маленький")
                    if attempt < Config.MAX_RETRIES - 1:
                        time.sleep(Config.RETRY_DELAY)
                        continue
                    return False
                
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка (попытка {attempt + 1}): {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY)
                    continue
                return False
        
        return False
    
    # ================================================================
    # ШАГ 2: Извлечение блока поезда - ТОЧНО КАК В workv2.sh
    # ================================================================
    def extract_train_block(self) -> bool:
        """
        Извлечение блока поезда - ТОЧНО КАК В workv2.sh
        """
        try:
            if not self.paths['parsed_html'].exists():
                self.logger.error(f"❌ Файл {self.paths['parsed_html']} не найден")
                return False
            
            with open(self.paths['parsed_html'], 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Экранируем номер поезда
            train_escaped = re.escape(self.train_number)
            
            # Находим начало блока - как в workv2.sh
            pattern = rf'data-number="{train_escaped}'
            match = re.search(pattern, content)
            
            if not match:
                self.logger.error(f"❌ Поезд {self.train_number} не найден")
                trains = re.findall(r'data-number="([^"]+)"', content)
                if trains:
                    unique_trains = list(dict.fromkeys(trains))
                    self.logger.info(f"📋 Доступные поезда: {', '.join(unique_trains[:10])}")
                return False
            
            start_pos = match.start()
            
            # Ищем открывающий div с классом train (как в workv2.sh)
            before = content[:start_pos]
            train_start = re.search(r'<div class="train train_seats[^>]*>', before[::-1])
            
            if not train_start:
                train_start = re.search(r'<div[^>]*class="[^"]*train[^"]*"[^>]*>', before[::-1])
            
            if train_start:
                block_start = start_pos - train_start.start()
            else:
                train_start = re.search(r'<div class="train train_seats[^>]*>', content)
                if train_start:
                    block_start = train_start.start()
                else:
                    self.logger.error("❌ Не найден блок train")
                    return False
            
            self.logger.info(f"✅ Начало блока на позиции {block_start}")
            
            # Ищем конец блока - как в workv2.sh
            next_train = re.search(r'<div class="train train_seats[^>]*>', content[block_start + 1:])
            
            if next_train:
                block_end = block_start + 1 + next_train.start()
                self.logger.info(f"✅ Конец блока на позиции {block_end}")
            else:
                end_match = re.search(r'</div>\s*</div>\s*</div>\s*$', content[block_start:])
                if end_match:
                    block_end = block_start + end_match.end()
                else:
                    block_end = len(content)
                self.logger.info(f"✅ Конец блока на позиции {block_end}")
            
            # Вырезаем блок
            train_block = content[block_start:block_end]
            
            # Добавляем заголовок как в workv2.sh
            header = f"""<!-- ======================================== -->
<!-- ПОЕЗД №{self.train_number}                     -->
<!-- {self.train_number} Москва — Симферополь -->
<!-- ДАТА: 30 сен, ср -->
<!-- ======================================== -->

"""
            
            with open(self.paths['train_html'], 'w', encoding=self.encoding) as f:
                f.write(header + train_block)
            
            file_size = os.path.getsize(self.paths['train_html'])
            self.logger.info(f"✅ Блок сохранён в {self.paths['train_html']}, размер: {file_size:,} байт")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    # ================================================================
    # ШАГ 3: Парсинг мест - ТОЧНО КАК В ex6.sh
    # ================================================================
    def parse_seats(self) -> Dict[str, Dict[str, int]]:
        """
        Парсинг мест - ТОЧНАЯ КОПИЯ ex6.sh
        """
        result = {}
        
        try:
            if not self.paths['train_html'].exists():
                self.logger.error(f"❌ Файл {self.paths['train_html']} не найден")
                return result
            
            # Читаем файл
            with open(self.paths['train_html'], 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # ============================================================
            # 1. Находим все строки с "seats_item" (КАК В ex6.sh)
            # ============================================================
            self.logger.info("🔍 Поиск seats_item...")
            
            # Находим все позиции seats_item
            seats_positions = []
            for match in re.finditer(r'seats_item', content):
                seats_positions.append(match.start())
            
            if not seats_positions:
                self.logger.error("❌ seats_item не найдены")
                return result
            
            self.logger.info(f"✅ Найдено {len(seats_positions)} seats_item")
            
            # ============================================================
            # 2. Для каждого seats_item извлекаем данные (КАК В ex6.sh)
            # ============================================================
            for idx, pos in enumerate(seats_positions):
                self.logger.info(f"  Обработка seats_item #{idx + 1}")
                
                # Берём блок из 15 строк (КАК В ex6.sh)
                # В ex6.sh: sed -n "${line_num},$((line_num+15))p"
                # Ищем конец строки
                line_start = content.rfind('\n', 0, pos) + 1
                line_num = content.count('\n', 0, line_start) + 1
                
                # Берём блок из 15 строк
                lines = content.split('\n')
                block_start = max(0, line_num - 1)
                block_end = min(len(lines), line_num + 15)
                block = '\n'.join(lines[block_start:block_end])
                
                # Ищем seats_line (КАК В ex6.sh)
                # В ex6.sh: echo "$block" | grep -A 1 "train_seats_count" | tail -1
                seats_line = None
                for i, line in enumerate(lines[block_start:block_end]):
                    if 'train_seats_count' in line:
                        if i + 1 < len(lines[block_start:block_end]):
                            seats_line = lines[block_start:block_end][i + 1]
                        break
                
                if not seats_line:
                    self.logger.warning(f"    ⚠️ train_seats_count не найдена")
                    continue
                
                self.logger.debug(f"    seats_line: {seats_line}")
                
                # Парсим как в ex6.sh
                # В ex6.sh: seats=$(echo "$seats_line" | sed 's/&nbsp;/ /g' | grep -o '[0-9]*' | grep -v '^$')
                # Заменяем &nbsp; на пробел
                seats_line_clean = seats_line.replace('&nbsp;', ' ')
                
                # Находим все числа
                numbers = re.findall(r'\d+', seats_line_clean)
                self.logger.debug(f"    numbers: {numbers}")
                
                lower = 0
                upper = 0
                
                # В ex6.sh: если 2 числа - первое нижние, второе верхние
                if len(numbers) >= 2:
                    lower = int(numbers[0])
                    upper = int(numbers[1])
                elif len(numbers) == 1:
                    lower = int(numbers[0])
                    upper = 0
                
                # Находим название типа вагона (КАК В ex6.sh)
                # В ex6.sh: type_name передаётся в функцию, но мы извлекаем из блока
                type_name = "Неизвестно"
                
                # Ищем train_places_name в блоке
                for line in lines[block_start:block_end]:
                    if 'train_places_name' in line:
                        name_match = re.search(r'>([^<]+)<', line)
                        if name_match:
                            type_name = name_match.group(1).strip()
                            break
                
                self.logger.info(f"    {type_name}: нижних {lower}, верхних {upper}")
                
                result[type_name] = {
                    'lower': lower,
                    'upper': upper,
                    'total': lower + upper,
                    'text': seats_line_clean
                }
            
            if result:
                self.logger.info(f"✅ Всего найдено {len(result)} типов вагонов")
            else:
                self.logger.error("❌ Не удалось найти информацию о местах")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при парсинге мест: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return result
    
    def save_results(self, seats_data: Dict[str, Dict[str, int]]) -> bool:
        """Сохранение результатов"""
        try:
            with open(self.paths['result_file'], 'w', encoding=self.encoding) as f:
                for class_name, data in seats_data.items():
                    f.write(f"{class_name}: нижних {data['lower']}, верхних {data['upper']}\n")
            
            self.logger.info(f"💾 Результаты сохранены в {self.paths['result_file']}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения: {e}")
            return False
    
    def check_changes(self) -> Tuple[bool, List[str]]:
        """Проверка изменений - как в tgbot_scrn.sh"""
        try:
            if not self.paths['result_file'].exists():
                return False, []
            
            # Извлекаем только строку с Плацкарт (как в tgbot_scrn.sh)
            # В tgbot_scrn.sh: grep "Плацкарт: нижних" "$result" > "$out"
            with open(self.paths['result_file'], 'r', encoding=self.encoding) as f:
                all_lines = f.readlines()
            
            current = []
            for line in all_lines:
                if 'Плацкарт: нижних' in line:
                    current = [line.strip()]
                    break
            
            if not current:
                current = all_lines
            
            previous = []
            if self.paths['snapshot_file'].exists():
                with open(self.paths['snapshot_file'], 'r', encoding=self.encoding) as f:
                    prev_lines = f.readlines()
                for line in prev_lines:
                    if 'Плацкарт: нижних' in line:
                        previous = [line.strip()]
                        break
                if not previous:
                    previous = prev_lines
            
            changes = []
            for i, line in enumerate(current):
                if i < len(previous) and line != previous[i]:
                    changes.append(f"Строка {i+1}: {previous[i]} -> {line}")
            
            if len(current) != len(previous):
                changes.append(f"Количество строк: {len(previous)} -> {len(current)}")
            
            return len(changes) > 0, changes
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки изменений: {e}")
            return False, []
    
    def send_telegram_message(self, message: str) -> bool:
        """Отправка сообщения в Telegram"""
        if not Config.SEND_MESSAGE:
            return True
        
        try:
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage"
            payload = {
                'chat_id': Config.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("✅ Сообщение отправлено")
                return True
            else:
                self.logger.error(f"❌ Ошибка: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}")
            return False
    
    def send_screenshot(self) -> bool:
        """Отправка скриншота"""
        if not Config.SEND_SCREENSHOT:
            return True
        
        try:
            if not self.paths['screenshot_file'].exists():
                return False
            
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendDocument"
            with open(self.paths['screenshot_file'], 'rb') as f:
                files = {'document': f}
                data = {'chat_id': Config.TELEGRAM_CHAT_ID}
                response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                self.logger.info("✅ Скриншот отправлен")
                return True
            else:
                self.logger.error(f"❌ Ошибка: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}")
            return False
    
    def take_screenshot(self) -> bool:
        """
        Создание скриншота с увеличенным масштабом
        """
        try:
            if not self.driver and not self.setup_driver():
                return False
            
            # Делаем скриншот
            self.driver.save_screenshot(str(self.paths['screenshot_file']))
            
            # Проверяем размер файла
            file_size = os.path.getsize(self.paths['screenshot_file'])
            self.logger.info(f"📸 Скриншот сохранён, размер: {file_size:,} байт")
            
            # Если файл слишком маленький, возможно масштаб не применился
            if file_size < 100000:  # Меньше 100KB
                self.logger.warning("⚠️ Скриншот получился маленьким, пробуем сделать снова...")
                # Пробуем сделать скриншот с другим подходом
                self.driver.execute_script("document.body.style.transform = 'scale(2)';")
                self.driver.execute_script("document.body.style.transformOrigin = '0 0';")
                time.sleep(1)
                self.driver.save_screenshot(str(self.paths['screenshot_file']))
                new_size = os.path.getsize(self.paths['screenshot_file'])
                self.logger.info(f"📸 Повторный скриншот, размер: {new_size:,} байт")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания скриншота: {e}")
            return False
    
    def update_snapshot(self):
        """Обновление снимка - как в tgbot_scrn.sh"""
        try:
            if self.paths['result_file'].exists():
                with open(self.paths['result_file'], 'r', encoding=self.encoding) as src:
                    with open(self.paths['snapshot_file'], 'w', encoding=self.encoding) as dst:
                        dst.write(src.read())
                self.logger.info("💾 Снимок обновлён")
        except Exception as e:
            self.logger.error(f"❌ Ошибка: {e}")
    
    def print_summary(self, seats_data: Dict[str, Dict[str, int]]):
        """Вывод сводки"""
        self.logger.info("📊 СВОДКА ПО МЕСТАМ:")
        self.logger.info("=" * 50)
        
        if not seats_data:
            self.logger.info("❌ Данные отсутствуют")
            return
        
        for class_name, data in seats_data.items():
            self.logger.info(f"  🚃 {class_name}:")
            self.logger.info(f"     📉 Нижних: {data['lower']}")
            self.logger.info(f"     📈 Верхних: {data['upper']}")
            self.logger.info(f"     📊 Всего: {data['total']}")
            self.logger.info("")
        
        self.logger.info("=" * 50)
    
    def run(self) -> bool:
        """Основной метод"""
        self.logger.info("=" * 70)
        self.logger.info(f"🚂 ЗАПУСК МОНИТОРИНГА ПОЕЗДА {self.train_number}")
        self.logger.info(f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 70)
        
        try:
            # Шаг 1: Парсинг страницы (scrab.py)
            self.logger.info("\n🔹 ШАГ 1: Парсинг страницы")
            if not self.parse_page():
                self.logger.error("❌ Не удалось распарсить страницу")
                return False
            
            time.sleep(Config.STEP_DELAY)
            
            # Шаг 2: Извлечение блока поезда (workv2.sh)
            self.logger.info("\n🔹 ШАГ 2: Извлечение блока поезда")
            if not self.extract_train_block():
                self.logger.error("❌ Не удалось извлечь блок поезда")
                return False
            
            time.sleep(Config.STEP_DELAY)
            
            # Шаг 3: Парсинг мест (ex6.sh)
            self.logger.info("\n🔹 ШАГ 3: Парсинг информации о местах")
            seats_data = self.parse_seats()
            if not seats_data:
                self.logger.warning("⚠️ Не найдена информация о местах")
                return False
            
            self.print_summary(seats_data)
            
            # Шаг 4: Сохранение результатов
            self.logger.info("\n🔹 ШАГ 4: Сохранение результатов")
            if not self.save_results(seats_data):
                self.logger.error("❌ Не удалось сохранить результаты")
                return False
            
            time.sleep(Config.STEP_DELAY)
            
            # Шаг 5: Проверка изменений (tgbot_scrn.sh)
            self.logger.info("\n🔹 ШАГ 5: Проверка изменений")
            has_changes, changes = self.check_changes()
            
            # Шаг 6: Создание скриншота (с увеличенным масштабом)
            self.logger.info("\n🔹 ШАГ 6: Создание скриншота")
            self.take_screenshot()
            
            time.sleep(Config.STEP_DELAY)
            
            # Шаг 7: Отправка уведомлений (tgbot_scrn.sh)
            self.logger.info("\n🔹 ШАГ 7: Отправка уведомлений")
            if has_changes:
                self.logger.info(f"✅ Обнаружены изменения: {len(changes)}")
                
                message = f"🚂 <b>Изменения в поезде {self.train_number}</b>\n\n"
                message += f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                message += "<b>Текущие данные:</b>\n<pre>\n"
                
                with open(self.paths['result_file'], 'r', encoding=self.encoding) as f:
                    message += f.read()
                
                message += "</pre>\n\n<b>Изменения:</b>\n<pre>\n"
                message += '\n'.join(changes)
                message += '</pre>'
                
                self.send_telegram_message(message)
                self.send_screenshot()
                
                for change in changes:
                    self.logger.info(f"  📝 {change}")
            else:
                self.logger.info("✅ Изменений не обнаружено")
            
            # Шаг 8: Обновление снимка
            self.logger.info("\n🔹 ШАГ 8: Обновление снимка")
            self.update_snapshot()
            
            self.logger.info("\n" + "=" * 70)
            self.logger.info("✅ МОНИТОРИНГ УСПЕШНО ЗАВЕРШЁН")
            self.logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("🔚 Драйвер закрыт")


def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("Использование: python3 train_monitor.py [номер_поезда]")
            sys.exit(0)
        Config.TRAIN_NUMBER = sys.argv[1]
    
    try:
        import selenium
        import requests
        import webdriver_manager
    except ImportError as e:
        print(f"❌ Ошибка: {e}")
        print("Установите: pip3 install selenium webdriver-manager requests")
        sys.exit(1)
    
    monitor = TrainMonitor()
    success = monitor.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
