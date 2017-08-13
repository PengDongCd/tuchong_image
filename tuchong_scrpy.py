import json
import os
from hashlib import md5
from requests import RequestException
from config import *
import requests
from urllib.parse import urlencode
from multiprocessing import Pool

def get_more_tag_pages(page_index):
    params = {
        'page': page_index,
        'count': 20,
        'order': 'weekly',
        'before_timestamp': None
    }
    url = "https://tuchong.com/rest/tags/" + TAG_NAME + "/posts?" + urlencode(params)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print("Response code is not 200 but ", response.code)
            return None
    except RequestException:
        print("Request Failed", RequestException)
        return None


def parse_tag_page(html):
    data = json.loads(html)
    if data and 'postList' in data.keys():
        for post in data.get('postList'):
            author_id = post.get('author_id')
            if post.get('images'):
                image_ids = [x.get('img_id') for x in post.get('images')]
                for image_id in image_ids:
                    yield {
                        'author_id': author_id,
                        'image_id': image_id
                    }
            else:
                print("there is no images in post" )
    else:
        print("There is no posts")


def dowload_images(image):
    author_id = image.get('author_id')
    image_id = image.get('image_id')
    url = "https://photo.tuchong.com/" + author_id + "/f/" + str(image_id) + ".jpg"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        else:
            print("Response code is not 200 but ", response.code)
            return None
    except RequestException:
        print("Request Failed", RequestException)
        return None


def save_image(content):
    file_dir = '{0}/{1}'.format(os.getcwd(), TAG_NAME)
    if not os.path.exists(file_dir): os.mkdir(file_dir)
    file_path = '{0}/{1}.{2}'.format(file_dir, md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()


def main(page_index):
    html = get_more_tag_pages(page_index)
    for image in parse_tag_page(html):
        dowload_images(image)

if __name__ == '__main__':
    indices = range(START_INDEX, END_INDEX)
    pool = Pool()
    pool.map(main, indices)





