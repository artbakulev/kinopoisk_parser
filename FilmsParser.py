import time
import os
import json

import bs4
import requests
import re


class FilmsParser:
    BASE = './pages/'
    BASE_LINK = 'https://wwww.kinopoisk.ru'
    image_link = re.compile(r".*\('(.+)'\).*")

    def __init__(self):
        self.links = []
        self.films = []
        self.files_names = []
        self.result_file = './result.json'
        self.films = []

    def _get_files_names(self):
        self.files_names = os.listdir(path=self.BASE)

    def _get_films_links(self, link='https://www.kinopoisk.ru/top/'):
        """Парсит ссылки на фильмы"""
        page = requests.get(link)
        bs = bs4.BeautifulSoup(page.text, features="html.parser")
        trs = bs.find_all(id=re.compile("top250_place_[0-9]*"))
        self.links = [tr.find('a', class_='all')['href'] for tr in trs]

    def _get_page_info(self, page):
        """Парсит страницу фильма"""
        page = bs4.BeautifulSoup(page, features='html.parser')
        data = {}
        movie_info = page.find('div', class_='movie-info')
        assert movie_info is not None
        data['image_link'] = self.BASE_LINK + self.image_link.search(
            movie_info.find('a', class_='popupBigImage')['onclick']).group(1)
        data['title'] = movie_info.find(class_='moviename-title-wrapper').text
        table_info = movie_info.find(class_='movie-info__table-container')
        info = table_info.find('table', class_='info')
        actors = table_info.find(id='actorList').find('ul').find_all('li')
        data['actors'] = [item.text for item in actors if item.text != '...']
        genres = info.find('span', itemprop='genre').find_all('a')
        data['genre'] = [item.text for item in genres if item.text != '...']
        data['description'] = page.find('div', itemprop='description').text
        trs = info.find_all('tr')
        keys = ['year', 'country']
        for i, key in enumerate(keys):
            try:
                if i == 2:
                    data[key] = trs[i].find_all('td')[1].text.strip().replace('\n', '')
                else:
                    data[key] = trs[i].find('a').text.strip().replace('\n', '')
            except AttributeError:
                continue
        self.films.append(data)

    @staticmethod
    def get_result_cinsear_json(inp, output):
        """форматирует JSON файл для соответствия cinsear формату"""
        with open(inp, "r") as f:
            body = json.load(f)
        items = []
        for item in body:
            formatted_item = {"title": item["title"], "description": item["description"], "year": item["year"],
                              "countries": item["country"], "genres": item["genre"]}
            items.append(formatted_item)
        with open(output, "w") as f:
            json.dump(items, f, ensure_ascii=False, indent=4)

    def _write_JSON(self, data):
        """дампит json"""
        with open(self.result_file, 'a') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _parse_films(self):
        """парсит все страницы фильмов, которые указаны в self.files_names"""
        for i, file in enumerate(self.files_names):
            print(i + 1, ' from ', len(self.files_names))
            with open(self.BASE + file, 'r') as f:
                self._get_page_info(f.read())
        print('writing JSON...')
        self._write_JSON(self.films)
        print('wrote JSON')

    def get_films_with_limit_and_offset(self, limit, offset):
        """отдает фильмы с лимитом и оффсетом"""
        with open(self.result_file, "r") as f:
            body = json.load(f)
        return body[offset:limit]

    def get_result_json(self, filename="./result.json"):
        """парсит и записывает фильмы в файл"""
        self.result_file = filename
        with open(self.result_file, "w") as f:
            pass
        self._get_files_names()
        self._parse_films()
