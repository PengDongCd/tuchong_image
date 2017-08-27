import json
import os
from hashlib import md5

import pymysql
from requests import RequestException
from config import *
import requests
from urllib.parse import urlencode
from multiprocessing import Pool


db = pymysql.connect("localhost","testuser01","test123456","TESTDB" )
cursor = db.cursor()

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


def get_post_data(html):
    data = json.loads(html)
    if data and 'postList' in data.keys():
        for post in data.get('postList'):
            author_id = post.get('author_id')
            post_id = post.get('post_id')
            if post.get('images'):
                yield {
                    'author_id': author_id,
                    'post_id': post_id
                }
            else:
                print("there is no images in post" )
    else:
        print("There is no posts")


def get_post_images_exif_data(post):
    author_id = post.get('author_id')
    post_id = post.get('post_id')
    url = "https://tuchong.com/rest/posts/" + post_id
    #cookies = dict(token='a495f70dd602560a')
    #cookies = dict(PHPSESSID='lb1dclr7rrn95241daacc4iqi0; webp_enabled=1', log_web_id='5000908063', token='a495f70dd602560a', _ga='GA1.2.1899690802.1503817215', _gid='GA1.2.811064440.1503817215')
    try:
        response = requests.get(url)
        if response.status_code == 200:
            if response.text == '':
                print("Response Text is empty!")
                return None
            data = json.loads(response.text)
            if data and 'images' in data.keys():
                for image in data.get('images'):
                    img_id = image.get('img_id')
                    if 'exif' in image.keys():
                        exif = image.get('exif')
                        if 'camera' in exif.keys() and 'lens' in exif.keys():
                            camera = exif.get('camera').get('name')
                            lens = exif.get('lens').get('name')
                            yield {
                                'author_id': author_id,
                                'img_id': img_id,
                                'camera': camera,
                                'lens': lens
                            }
                        elif 'camera' in exif.keys() and 'len' not in exif.keys():
                            camera = exif.get('camera').get('name')
                            lens = None
                            yield {
                                'author_id': author_id,
                                'img_id': img_id,
                                'camera': camera,
                                'lens': lens
                            }
                        elif 'camera' not in exif.keys() and 'len' in exif.keys():
                            lens = exif.get('lens').get('name')
                            camera = None
                            yield {
                                'author_id': author_id,
                                'img_id': img_id,
                                'camera': camera,
                                'lens': lens
                            }
                        else:
                            print("there is no camera and lens data!")
                    else:
                        print("there is no exif in this image!")
            else:
                print("There is no images in this post!")

        else:
            print("Response code is not 200 but ", response.code)
            return None
    except RequestException:
        print("Request Failed", RequestException)
        return None


def save_exif_data_to_mysql(content):
    sql = "INSERT INTO tuchong_camera_data \
            (image_id,auth_id, CAMERA, LENS) \
         VALUES ('%d', '%d', '%s', '%s')" % \
          (content['img_id'], int(content['author_id']), content['camera'], content['lens'])

    try:
        # 执行sql语句
        cursor.execute(sql)
        # 执行sql语句
        db.commit()
        print("data has been saved to DB!")
    except:
        # 发生错误时回滚
        db.rollback()

def main(page_index):
    html = get_more_tag_pages(page_index)
    for post in get_post_data(html):
        for image in get_post_images_exif_data(post):
            save_exif_data_to_mysql(image)



if __name__ == '__main__':
    indices = range(START_INDEX, END_INDEX)
    pool = Pool()
    pool.map(main, indices)





