from PersonParser import PersonParser
from FilmsParser import FilmsParser
from Saver import Saver
import common
import json

with open('persons_finish.json') as f:
    data = json.load(f)

links = []
for i in data:
    links.append(i['image_link'])


with open('persons_data_images.json', 'w') as f:
    json.dump(links, f, indent=4, ensure_ascii=False)
