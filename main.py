import sys
import json
import os
import shutil
import random
import string
from time import sleep, time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options


class MainSelenium:
    URL = None

    def __init__(self, driver):
        self.driver = driver

    def _wait_elems(self, xpath, timeout=5):
        """Функция ожидания элементов"""
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))

    def _wait_staleness(self, xpath, timeout=5):
        """Функция ожидания устаревания элементов"""
        try:
            WebDriverWait(self.driver, timeout).until(EC.staleness_of(self._wait_elems(xpath)[0]))
        except TimeoutException:
            pass

    def interaction_with(self, xpath, timeout=5, wait_for_staleness=False, clickable=False, scroll=False, click=False, text=None):
        """ Функция взаимодействия с элементомами. Возвращает запрошенный элемент """
        # Дожидаемся появления элемента на странице

        if wait_for_staleness:
            self._wait_staleness(xpath, timeout)

        elems = self._wait_elems(xpath, timeout)

        # Проверяем сколько элементов обнаружено
        if len(elems) > 1:
            # Если найдена группа элементов, то возвращаем список элементов
            return elems
        else:
            # Иначе - начинаем взаимодействие
            elem = elems[0]

        if clickable:
            # Дожидаемся кликабельности элемента
            WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))

        if scroll:
            # Скроллим элемент в пределы видимости:
            elem.location_once_scrolled_into_view

        if click:
            # Нажимаем на элемент
            elem.click()
        if text is not None:
            # Вводим текст
            elem.send_keys(text)
        time_sleep = random.randint(2000, 3500)/1000
        sleep(time_sleep)
        return elem

    def visibility(self, xpath, timeout):
        """Функция ожидания появления загрузочного элемента"""
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))

    def invisibility(self, xpath, timeout):
        """Функция ожидания исчезновения загрузочного элемента"""
        WebDriverWait(self.driver, timeout).until_not(EC.presence_of_element_located((By.XPATH, xpath)))


class Registration(MainSelenium):
    URL = "https://www.sciencedirect.com/browse/journals-and-books?contentType=JL&accessType=openAccess&subject=social-sciences-and-humanities"

    def registration(self, data):
        """Функция регистрации аккаунта"""
        # Заходим на сайт
        self.driver.get(self.URL)

        # Находим по xpath  кнопку "Register", нажимаем
        self.interaction_with('(//span[@class="link-button-text"])[1]', wait_for_staleness=True, clickable=True, click=True)

        # Находим по xpath поле "email", вводим email
        self.interaction_with('//input[@name="pf.username"]', text=data.EMAIL)

        # Находим по xpath кнопку "Продолжить", нажимаем
        self.interaction_with('//button[@class="els-primaryBtn"]', scroll=True, clickable=True, click=True)

        # Находим по xpath поле "Имя", вводим имя
        self.interaction_with('//input[@name="givenName"]', clickable=True, text=data.NAME)

        # Находим по xpath поле "Фамилия", вводим фамилию
        self.interaction_with('//input[@name="familyName"]',  clickable=True, text=data.LAST_NAME)

        # Находим по xpath поле "Пароль", вводим пароль
        self.interaction_with('//input[@name="pf.pass"]',  clickable=True, text=data.PASSWORD)

        # Находим по xpath кнопку "Зарегистрироваться", кликаем на нее
        self.interaction_with('//*[@id="bdd-elsPrimaryBtn"]', scroll=True, clickable=True, click=True)

        # Находим по xpath кнопку "Перейти к ScienceDirect",  кликаем на нее
        self.interaction_with('//button[@name="register_continue"]', timeout=10, scroll=True, clickable=False, click=True)


class Downloader(MainSelenium):
    URL = "https://www.sciencedirect.com/browse/journals-and-books?contentType=JL&accessType=openAccess&subject=social-sciences-and-humanities"

    def remove_elem(self, element):
        """Функция удаления элемента со страницы"""
        self.driver.execute_script("""
        var element = arguments[0];
        element.parentNode.removeChild(element);
        """, element)

    def enter_books(self, book, book_name):
        """Функция входа в книгу"""
        actions = ActionChains(self.driver)
        actions.key_down(Keys.CONTROL).click(book).key_up(Keys.CONTROL).perform()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        print("Загрузка книги: " + book_name)
        self.interaction_with('//input[@class="search-input"]', wait_for_staleness=True, clickable=True, click=True)
        self.interaction_with('//button[@class="button submit-search-button button-primary"]', wait_for_staleness=True, clickable=True, scroll=True, click=True)
        self.interaction_with('//a[@data-aa-name="srp-100-results-per-page"]', clickable=True, scroll=True, click=True)
        element = self.interaction_with('//div[@class="Feedback-Container"]', clickable=True, click=False)
        self.remove_elem(element)

    def find_art_links(self):
        """Функция для поиска всех файлов на странице"""
        articles = self.interaction_with('//li[@class="DownloadPdf download-link-item"]//a[@class="download-link"]',
                                         wait_for_staleness=True, clickable=True, scroll=True)
        art_links = []
        if isinstance(articles, WebElement):
            articles = [articles]

        for art in articles:
            art_link = art.get_attribute("href")
            art_links.append(art_link)


        return art_links

    def make_directory(self, main_directory, book_name):
        """Функция создания директории с названием книги"""
        path = os.path.join(main_directory, book_name)
        os.mkdir(path)
        return path

    def add_book_name(self, book, main_directory):
        """Функция добавления имени книги в словарь """
        book_name = book.text
        if ":" in book_name:
            book_name = book_name.replace(":", "_")
        with open('books_and_articles.json', 'r', encoding="utf-8") as f:
            json_data = json.load(f)
            if book_name not in json_data:
                json_data[book_name] = []
                self.make_directory(main_directory, book_name)
        with open('books_and_articles.json', 'w', encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
            f.close()

        return book_name

    def add_article_link(self, art_link, book_name=None):
        """Функция добавления ссылки на файл в словарь"""

        with open('books_and_articles.json', 'r', encoding="utf-8") as f:
            json_data = json.load(f)
            if art_link not in json_data[book_name]:
                json_data[book_name].append(art_link)
                add_link = True
            else:
                add_link = False
        with open('books_and_articles.json', 'w', encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
            f.close()

        return add_link

    def download_articles(self, art_link, download_dir, main_directory, book_name):
        """Функция загрузки файлов(артиклей)"""
        self.driver.execute_script('window.open();')
        tries = 0
        while len(self.driver.window_handles) < 3:
            sleep(0.1)
            tries += 1
            if tries > 10:
                raise ValueError('New tab was not opened...')
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(art_link)

        self.replace_articles(download_dir, main_directory, book_name)
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[1])

    def replace_articles(self, download_dir, main_directory, book_name):
        """Функция перемещения файлов в директорию с названием соответствующей книги"""
        tries = 0
        while tries < (30 / 0.1):  # max seconds to wait / 0.1 (sleep time)
            if len(os.listdir(download_dir)) > 0:
                file = os.listdir(download_dir)[0]
                if file.endswith('.pdf'):
                    break
            tries += 1
            sleep(0.1)
        else:
            return

        path1 = os.path.join(download_dir, file)
        path2 = os.path.join(main_directory, book_name, file)
        os.replace(path1, path2)
        print("Файл " + file + " сохранен в: " + path2)

    def stop_script(self, user_len_download_articles):
        """Функция остановки скрипта"""
        print("Вы загрузили " + str(user_len_download_articles) + " файлов, чтобы продолжить - нажмите Enter, чтобы завершить работу программы - нажмите 'q' и Enter: ")
        while True:
            command = input('-> ')
            if command == "":
                print("Продолжаем...")
                stop_script = False
                break
            elif command == "q":
                print("Завершаем загрузку файлов...")
                self.driver.quit()
                stop_script = True
                break
            else:
                print("Вы ввели неверное значение, повторите ввод")

        return stop_script

    def processing_books(self, download_dir, main_directory):
        """Функция обработки книг на странице. Добавляем в словарь имя книги, заходим в книгу, добавляем в словарь ссылку\
         на файл, скачиваем файл"""
        # Переходим по ссылке с выбранными фильтрами
        self.driver.get(self.URL)
        user_len_download_articles = int(input("Какое количество файлов вы хотите скачать?(введите число): "))
        len_downloaded_articles = 0
        while True:
            books_on_page = self.interaction_with("//div//ol[@id='publication-list']//li//a[@href]", wait_for_staleness=True,
                                                  clickable=True, scroll=True, click=False, text=None)
            for book in books_on_page:
                book_name = self.add_book_name(book, main_directory)
                self.enter_books(book, book_name)
                book_index = True
                while book_index == True:
                    try:
                        art_links = self.find_art_links()
                        for art_link in art_links:
                            add_link = self.add_article_link(art_link, book_name)
                            if add_link == True and len_downloaded_articles < user_len_download_articles:
                                self.download_articles(art_link, download_dir, main_directory, book_name)
                                len_downloaded_articles += 1
                            elif len_downloaded_articles >= user_len_download_articles:
                                stop_script = self.stop_script(user_len_download_articles)
                                len_downloaded_articles = 0
                                if stop_script == False:
                                    user_len_download_articles = int(input("Какое количество файлов вы хотите скачать?(введите число): "))
                                    continue
                                else:
                                    sys.exit()

                        self.interaction_with('//li[@class="pagination-link next-link"]', scroll=True,
                                              clickable=True, click=True)
                    except TimeoutException:
                        book_index = False
                        print("Все файлы книги " + book_name + " загружены")
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                continue
            try:
                self.interaction_with('//button[@aria-label="Next page"]', scroll=True, clickable=True, click=True)
            except TimeoutException:
                print("Все книги загружены")
                break


class Data:
    letters = string.ascii_lowercase
    rand_letters = "".join(random.choices(letters, k=8))
    EMAIL = rand_letters + "@gmail.com"
    PASSWORD = "venividivici"
    TEL = '0509917818'
    NAME = "Дмитрий"
    LAST_NAME = "Пономаренко"
    PAROL = "venividivici"


def tabs_cleaner(driver):
    start_time = time()
    while len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        driver.close()
        print('Useless tab was closed...')
        if (time()-start_time) > 10:
            raise ValueError("Can't close useless tabs...")
    driver.switch_to.window(driver.window_handles[0])


def take_screenshot(driver):
    name = 'screenshot_{}.png'
    c = 1
    while os.path.exists(name.format(c)):
        c += 1
    driver.save_screenshot(name.format(c))


def main():
    USE_HEADLESS = False
    directory = "C:\\Users\\Lola\\PycharmProjects\\science"
    main_directory = os.path.join(directory, 'downloaded_books')
    download_dir = os.path.join(directory, 'downloads')
    profile_dir_bcp = os.path.join(directory, 'profile_bcp')
    profile_dir = os.path.join(directory, 'profile')

    if os.path.exists(profile_dir):
        shutil.rmtree(profile_dir)
    shutil.copytree(profile_dir_bcp, profile_dir)

    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)
        os.mkdir(download_dir)

    if not os.path.exists(main_directory):
        os.mkdir(main_directory)

    chrome_options = Options()
    preferences = {"download.default_directory": download_dir,
                   "download.prompt_for_download": False,
                   "download.directory_upgrade": True,
                   "plugins.always_open_pdf_externally": True}
    chrome_options.add_experimental_option("prefs", preferences)

    if USE_HEADLESS:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--window-size=1440x900")
        chrome_options.add_argument('start-maximized')
        chrome_options.add_argument('disable-infobars')
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36")

    chrome_options.add_argument("user-data-dir={}".format(profile_dir))

    driver = webdriver.Chrome(options=chrome_options)

    try:
        if not USE_HEADLESS:
            driver.maximize_window()
        data = Data()
        tabs_cleaner(driver)
        registration = Registration(driver)
        registration.registration(data)
        downloader = Downloader(driver)
        downloader.processing_books(download_dir, main_directory)
    finally:
        print('Exit.')
        # take_screenshot(driver)
        # driver.quit()


if __name__ == '__main__':
    main()
