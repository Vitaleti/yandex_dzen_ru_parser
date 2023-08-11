import json
import os
import uuid
from time import sleep
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime


def get_subtitle(driver):
    # Получаем HTML содержимое новостной страницы
    page_source = driver.page_source

    # Создаем объект BeautifulSoup для парсинга HTML
    soup = BeautifulSoup(page_source, "html.parser")
    subtitles = soup.find('div', class_="mg-snippets-group").find_all('span', class_="mg-snippet__text")
    subtitles = ', '.join(subtitle.text for subtitle in subtitles)

    return subtitles


def get_subtitle_other(driver):
    print(driver.current_url)
    # Делаем клик по кнопке "показать ещё"
    try:
    	button = driver.find_element(By.CSS_SELECTOR, '[aria-label="Показать ещё новости"]').click()
    except:
    	sub_others = "no additional headings"
    	return sub_others

    # Получаем HTML содержимое новостной страницы
    page_source = driver.page_source

    # Создаем объект BeautifulSoup для парсинга HTML
    soup = BeautifulSoup(page_source, "html.parser")
    sub_others = soup.find('div', class_="mg-story__source").find_all('a', class_="mg-snippet__url")
    sub_others = ', '.join(sub_other.text for sub_other in sub_others)

    return sub_others


def save_image(image_url, rubric, datetime_str):
	# Создаем путь для сохранения изображения
	image_folder = os.path.join("images", rubric, datetime_str)
	os.makedirs(image_folder, exist_ok=True)
	image_path = os.path.join(image_folder, f"{uuid.uuid4()}")
	image_path += '.jpg'

	# Скачиваем изображение
	response = requests.get(image_url)
	with open(image_path, "wb") as f:
		f.write(response.content)


def create_json_file(data):
    # Генерируем уникальный uuid для имени файла
    file_uuid = str(uuid.uuid4()).replace('-', '')
    datetime_str = data["datetime"]

    # Формируем путь к JSON файлу
    json_path = f"json/{datetime_str}/{file_uuid}.json"

    # Убедимся, что директория для JSON файла существует
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # Сохраняем данные в JSON файл
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)


def get_source(url, driver):
	driver.get(url)

	# Скролинг вниз для прогрузки всей страницы
	driver.implicitly_wait(5)
	driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
	sleep(4)

	# Получение html кода страницы
	source = driver.page_source
	source = BeautifulSoup(source, "html.parser")

	# Получение списка блоков с нужным контентом
	news = source.find('div', class_='mg-grid__col mg-grid__col_xs_12')
	news = news.find_all('div', class_='mg-grid__col')

	# Получение названия рубрики
	rubric = urlparse(url).path.split('/')[-1]

	# Текущее время выполнения скрипта
	datetime_str = datetime.now().strftime("%Y%m%d%H%M%S%f")

	# Создаём словарь с данными
	data = {
		"datetime": datetime_str,
		"content": []
	}

	i = 0
	for new in news:
		try:
			title = new.find('a', class_='mg-card__link').text.strip() # Заголовок
		except AttributeError:
			continue
		link = new.find('a', class_='mg-card__link').get('href') # Ссылка
		image_hyperlink = new.find('div', class_='mg-card-media__image') # Ссылка на изображение

		# На проверка на одно из условий расположения ссылки на изображение
		if image_hyperlink is not None:
			image_hyperlink = image_hyperlink.find('img').get('src')
		else:
			image_hyperlink = str(new.find('div', class_="mg-card__media-block_type_image").get('style'))
			image_hyperlink = image_hyperlink[image_hyperlink.find('(') + 1: image_hyperlink.rfind(')')]
			image_hyperlink = image_hyperlink.replace('"', '')

		# Сохраняем изображение
		save_image(image_hyperlink, rubric, datetime_str)

		# Переход на страницу новости
		driver.get(link)

		subtitle = get_subtitle(driver)
		sub_other = get_subtitle_other(driver)

		data["content"].append({
			"title": title,
			"link": link,
			"subtitle": subtitle,
			"sub_other": sub_other,
			"image": image_hyperlink
		})

		print(title)
		print(link)
		print(image_hyperlink)
		i += 1
	print(i)

	create_json_file(data)
	

def main():
	with open('links.json') as file:
		urls = json.load(file)['urls']

	# Опции для Selenium, чтобы запустить браузер в фоновом режиме
	chrome_options = Options()
    # chrome_options.add_argument("--headless")
	chrome_options.add_argument("--window-size=1920x1080")

    # Инициализация драйвера Chrome
	driver = webdriver.Chrome(options=chrome_options)

	for url in urls:
		get_source(url, driver)

	# Закрыть драйвер
	driver.quit()


if __name__ == "__main__":
	main()