# -*- coding: utf-8 -*-
import common
from selenium import webdriver, common as com
import re
import json
import os
import bs4


class PersonParser:
    BASE_PAGE = "https://www.kinopoisk.ru/"
    SEARCH_FORM_CLASS = "kinopoisk-header-search-form-input__input"
    ALTERNATIVE_SEARCH_FORM_CLASS = "header-fresh-search-partial-component__field"
    SEARCH_SUGGEST_FIRST_CLASS = "js-serp-metrika"
    ACTOR_LINK_REGEXP = re.compile(".*/(name/[0-9]+/)")
    BASE_DIR = './pages/'

    def __init__(self, web=False):
        self.output_models_filename = "persons_parsed.json"
        self.output_links_filename = "persons_links_parsed.json"
        self.names = set()
        self.persons_name_link = []
        self.web = web
        self.persons = []
        self.filenames = os.listdir(self.BASE_DIR)
        if self.web:
            print("web option is set - launch browser")
            self.driver = webdriver.Chrome()
        else:
            print("no web option - only offline operations")

    def __del__(self):
        if self.web:
            self.driver.close()

    def get_links_by_names_from_file(self, filename, name_key, link_key):
        links = []
        with open(filename, 'r') as f:
            body = json.load(f)
        for person in body:
            name = person[name_key]
            if name in self.names:
                links.append(person[link_key])
        return links

    def get_persons_names(self, filename, key, is_file_nested=False):
        """забирает все различные имена персон из файла"""
        self.names = common.get_set_from_json(filename, key, is_file_nested)
        print('get {} different names'.format(len(self.names)))

    def subtract_persons_names(self, filename, key, is_file_nested=False):
        """обновляет имена персон из файла"""
        print('before subtraction: {} elements'.format(len(self.names)))
        names = common.get_set_from_json(filename, key, is_file_nested)
        self.names = names.symmetric_difference(self.names)
        print('after subtraction: {} elements'.format(len(self.names)))

    def dump_persons_links(self):
        """получает ссылку на актера через поиск и записывает их в виде json в файл"""
        self.driver.get(self.BASE_PAGE)
        search_form = self.driver.find_element_by_class_name(self.ALTERNATIVE_SEARCH_FORM_CLASS)
        search_form.send_keys("matrix")
        search_form.submit()
        if "Ой!" in self.driver.title:
            print("Enter the captcha!")
            input()
        f = open(self.output_links_filename + '.tmp', 'a')
        for i, person_name in enumerate(self.names):
            print("person {} from {} (in list {})".format(i, len(self.names), len(self.persons_name_link)))
            try:
                self.driver.implicitly_wait(0.5)
                search_form = self.driver.find_element_by_class_name(self.SEARCH_FORM_CLASS)
                search_form.clear()
                search_form.send_keys(person_name)
                search_form.submit()
                self.driver.implicitly_wait(0.3)
                link = self.ACTOR_LINK_REGEXP.search(
                    self.driver.find_element_by_class_name(self.SEARCH_SUGGEST_FIRST_CLASS).get_attribute("href"))[0]
                self.persons_name_link.append({"person": person_name, "link": link})
            except (com.exceptions.NoSuchElementException, IndexError, TypeError):
                self.driver.implicitly_wait(0.5)
                try:
                    link = self.ACTOR_LINK_REGEXP.search(
                        self.driver.find_element_by_class_name(self.SEARCH_SUGGEST_FIRST_CLASS).get_attribute("href"))[
                        0]
                    self.persons_name_link.append({"person": person_name, "link": link})
                except (com.exceptions.NoSuchElementException, IndexError, TypeError):
                    print("failed: " + person_name)
        f.close()
        with open(self.output_links_filename, "w") as f:
            json.dump(self.persons_name_link, f, ensure_ascii=False, indent=4)

    def parse_persons_from_pages_to_file(self, out):
        """парсит всех персон из файлов"""
        len_filenames = len(self.filenames)
        for i, filename in enumerate(self.filenames):
            print("parse {} file from {} ({})".format(i, len_filenames, filename))
            try:
                person = self._parse_person_from_file(self.BASE_DIR + filename)
                self.persons.append(person)
            except AssertionError:
                print("failed")
        with open(out, 'w') as f:
            json.dump(self.persons, f, indent=4, ensure_ascii=False)

    @staticmethod
    def _read_file(filename):
        with open(filename, "r") as f:
            page = f.read()
        return page

    @staticmethod
    def _map_career(career_ru):
        if career_ru == 'Актер' or career_ru == 'Актриса':
            return 'actor'
        if career_ru == 'Продюсер':
            return 'producer'
        if career_ru == 'Сценарист':
            return 'screenwriter'
        if career_ru == 'Режиссер':
            return 'director'
        if career_ru == 'Композитор':
            return 'composer'
        if career_ru == 'Монтажер':
            return 'editor'
        if career_ru == 'Оператор':
            return 'operator'

    def _parse_career(self, career_tr):
        if career_tr is None:
            return []
        career_tds = career_tr.find_all('td')
        assert "карьера" in career_tds[0]
        career_as = career_tds[1].find_all('a')
        career_roles = []
        for a in career_as:
            career_roles.append(self._map_career(a.text.strip()))
        return career_roles

    @staticmethod
    def _map_month_to_int(month):
        if month == 'января':
            return 1
        if month == 'февраля':
            return 2
        if month == 'марта':
            return 3
        if month == 'апреля':
            return 4
        if month == 'мая':
            return 5
        if month == 'июня':
            return 6
        if month == 'июля':
            return 7
        if month == 'августа':
            return 8
        if month == 'сентября':
            return 9
        if month == 'октября':
            return 10
        if month == 'ноября':
            return 11
        if month == 'декабря':
            return 12

    def _parse_birth(self, birth_td):
        if birth_td is None:
            return ''
        try:
            birth_as = birth_td.find_all('a')
            date = birth_as[0].text.split(' ')
            birth = date[0]
            birth += '.' + str(self._map_month_to_int(date[1])) + '.'
            birth += birth_as[1].text
        except IndexError:
            return ''
        return birth

    @staticmethod
    def _parse_birthplace(birthplace_tr):
        if birthplace_tr is None:
            return ''
        birthplace_as = birthplace_tr.find_all('td')[1].find_all('a')
        birthplace = ''
        for a in birthplace_as:
            birthplace += a.text + ','
        return birthplace[:len(birthplace) - 1]

    @staticmethod
    def add_id(inp, out):
        with open(inp, 'r') as f:
            data = json.load(f)
        for i, item in enumerate(data):
            item['id'] = i
        with open(out, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _parse_person_from_file(self, filename):
        """открывает файл и парсит одну персону"""
        source = self._read_file(filename)
        page = bs4.BeautifulSoup(source, features='html.parser')
        data = {}
        person_header = page.find('div', id='headerPeople')
        assert person_header is not None
        person_info = page.find(id='infoTable').find('tbody')
        assert person_info is not None
        data['name'] = person_header.find('h1').text.strip()
        person_info_trs = person_info.find_all('tr')
        data['roles'] = self._parse_career(person_info_trs[0])
        data['birthday'] = self._parse_birth(person_info_trs[2]).strip()
        data['birthplace'] = self._parse_birthplace(person_info_trs[3]).strip()
        data['image_link'] = page.find('div', id='photoBlock').find('img')['src']
        return data

    def map_persons_ids_to_films(self, persons_ids_filename, films_filename, output):
        with open(persons_ids_filename, 'r') as f:
            data = json.load(f)
        name_id = {}
        for person in data:
            name_id[person['name']] = person['id']
        with open(films_filename, 'r') as f:
            data = json.load(f)
        for film in data:
            actors = film['actors']
            tmp = []
            for actor in actors:
                try:
                    tmp.append(name_id[actor])
                except KeyError:
                    print('failed: ', actor)
            film['actors'] = tmp
        with open(output, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

