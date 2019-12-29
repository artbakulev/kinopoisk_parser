from selenium import webdriver
import os
import time


class Saver:
    def __init__(self, links):
        self.links = links
        self.driver = webdriver.Chrome()
        self.base = 'pages/'
        self.website = 'https://www.kinopoisk.ru/'
        self.files = set(os.listdir("pages/"))

    def __del__(self):
        self.driver.close()

    def _save_page(self, base, link):
        filename = link.split('/')[-2] + '.html'
        # if filename in self.files:
        #     print("skipped")
        #     return
        self.driver.get(link)

        with open(base + filename, 'w') as f:
            f.write(self.driver.page_source)

    def save_pages(self):
        if not os.path.exists(self.base):
            os.mkdir(self.base)
        for i, link in enumerate(self.links):
            print("link {} from {}".format(i, len(self.links)))
            self._save_page(self.base, self.website + link)
