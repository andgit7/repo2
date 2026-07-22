from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

class HeadlessParser:
    def __init__(self, url, html_file="output.html"):
        """
        Инициализация парсера
        
        Args:
            url (str): URL для парсинга
            html_file (str): имя файла для сохранения HTML
        """
        self.url = url
        self.html_file = html_file
        self.driver = None
        
    def setup_driver(self):
        """Настройка headless драйвера Chrome"""
        options = Options()
        
        # Настройки для headless режима
        options.add_argument("--headless=new")  # Новый headless режим
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Дополнительные опции для стабильности
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-setuid-sandbox")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Создаем драйвер
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            # Убираем флаг автоматизации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Ошибка при создании драйвера: {e}")
            raise
    
    def parse_page(self, wait_time=10):
        """
        Парсинг страницы и сохранение HTML
        
        Args:
            wait_time (int): время ожидания загрузки страницы в секундах
        
        Returns:
            str: HTML содержимое страницы
        """
        if not self.driver:
            self.setup_driver()
        
        try:
            print(f"Загрузка страницы: {self.url}")
            self.driver.get(self.url)
            
            # Ждем загрузки основного контента
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Дополнительная задержка для динамического контента
            time.sleep(2)
            
            # Получаем HTML страницы
            html_content = self.driver.page_source
            
            # Сохраняем в файл
            self.save_html(html_content)
            
            print(f"Парсинг успешно завершен. HTML сохранен в: {self.html_file}")
            return html_content
            
        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
            return None
    
    def save_html(self, html_content):
        """Сохранение HTML в файл"""
        try:
            with open(self.html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            print(f"Ошибка при сохранении HTML файла: {e}")
    
    def get_specific_content(self, selector, attribute=None):
        """
        Получение конкретного контента по селектору
        
        Args:
            selector (str): CSS селектор
            attribute (str): атрибут для извлечения (None для текста)
        
        Returns:
            list: список найденных элементов
        """
        if not self.driver:
            return None
        
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if attribute:
                return [elem.get_attribute(attribute) for elem in elements]
            return [elem.text for elem in elements]
        except Exception as e:
            print(f"Ошибка при получении контента: {e}")
            return []
    
    def close(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()
            print("Драйвер закрыт")


# Пример использования
def main():
    # Указываем URL и имя файла для сохранения
    url = "https://grandtrain.ru/search/2000000-2078001/30.09.2026/"  # Замените на нужный URL
    html_file = "/home/and/pars5/snapshot/parsed_page.html"  # Имя файла для сохранения HTML
    
    # Создаем парсер
    parser = HeadlessParser(url, html_file)
    
    try:
        # Парсим страницу
        html_content = parser.parse_page(wait_time=10)
        
        if html_content:
            print(f"Получен HTML размером: {len(html_content)} символов")
            
            # Пример получения заголовка страницы
            title = parser.get_specific_content("title")
            if title:
                print(f"Заголовок страницы: {title[0]}")
            
            # Пример получения всех ссылок
            links = parser.get_specific_content("a", "href")
            if links:
                print(f"Найдено ссылок: {len(links)}")
                # print(f"Первые 5 ссылок: {links[:5]}")
            
            # Пример получения всех заголовков h1
            headers = parser.get_specific_content("h1")
            if headers:
                print(f"Найдено заголовков h1: {len(headers)}")
                # print(f"Заголовки: {headers}")
        
    except Exception as e:
        print(f"Ошибка в процессе парсинга: {e}")
    
    finally:
        # Всегда закрываем драйвер
        parser.close()


if __name__ == "__main__":
    main()
