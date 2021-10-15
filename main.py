import requests
from pprint import pprint
import json
import os
import datetime
import PySimpleGUI as sg
import time
from tqdm import tqdm


def time_convert(time_unix):
    time_bc = datetime.datetime.fromtimestamp(time_unix)
    str_time = time_bc.strftime('%Y-%m-%d time %H-%M-%S')
    return str_time


class VkPhotoOwner:
    url = 'https://api.vk.com/method/'

    def __init__(self, owner_id):

        self.params = {
            'access_token': vk_token,
            'v': '5.131',
            'owner_id': owner_id
        }

    def download_vk_photos(self):
        get_photos_url = self.url + 'photos.get'
        get_photos_params = {
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1,
            'count': 1000
        }
        photos = requests.get(get_photos_url,
                              params={**self.params,
                                      **get_photos_params}). \
            json()['response']['items']
        for i in tqdm(photos, ascii=True,
                      desc="Получен ответ на https-request"):
            time.sleep(0.1)
        photo_dict = {}
        for photo in tqdm(photos,
                          desc="Формирование словаря по количеству лайков"):
            max_size_type = photo["sizes"][-1]["type"]
            photo_url = photo["sizes"][-1]["url"]
            likes_count = photo["likes"]["count"]
            photo_date = time_convert(photo["date"])
            value = photo_dict.get(likes_count, [])
            value.append({'date': photo_date,
                          'url': photo_url,
                          'size': max_size_type})
            photo_dict[likes_count] = value
        json_list = []
        list_for_download = []
        for item in tqdm(photo_dict.keys(),
                         desc="Получение структуры json-файла"
                              "и списка фото для загрузки"):
            for value in photo_dict[item]:
                if len(photo_dict[item]) == 1:
                    file_name = f'{item}.jpeg'
                else:
                    file_name = f'{item} {value["date"]}.jpeg'
                json_list.append({'file_name': file_name,
                                  'size': value['size']})
                list_for_download.append({'file_name': file_name,
                                          'url': value['url']})
        for i in tqdm(json_list, desc="Запись json-файла"):
            with open('json_file', 'w') as json_file:
                json.dump(json_list, json_file, indent=2, ensure_ascii=False)
        os.mkdir('Photo_Album')
        for element in tqdm(list_for_download,
                            desc="Загрузка фотографий в локальную папку"):
            with open(f'Photo_Album/{element["file_name"]}', 'bw') as file:
                resp_download = requests.get(element["url"], stream=True)
                for chunk in resp_download.iter_content(4096):
                    file.write(chunk)


class Yandex:
    def __init__(self, ya_token):
        self.ya_token = ya_token
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources'

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'OAuth {self.ya_token}'
        }

    def create_folder(self, path):
        headers = self.get_headers()
        requests.put(f'{self.url}?path={path}', headers=headers)

    def upload_file(self, loadfile, savefile, replace=False):
        headers = self.get_headers()
        res = requests.get(f'{self.url}/upload?'
                           f'path={savefile}&overwrite={replace}',
                           headers=headers).json()
        with open(loadfile, 'rb') as f:
            try:
                requests.put(res['href'], files={'file': f})
            except KeyError:
                print(res)

    def backup(self, savepath, loadpath):
        self.create_folder(savepath)
        for address, dirs, files in os.walk(loadpath):
            for i, file in enumerate(files):
                self.upload_file(f'{address}/{file}', f'{savepath}/{file}')
                sg.one_line_progress_meter('Процесс загрузки файлов '
                                           'на Яндекс Диск', i + 1, len(files),
                                           '-key-')
                time.sleep(1)


if __name__ == "__main__":
    with open('Vktoken.txt', 'r') as file:
        vk_token = file.read().strip()
    with open('Yatoken.txt') as file_obj:
        ya_token = file_obj.read().strip()
    vk_photo = VkPhotoOwner('552934290')
    vk_photo.download_vk_photos()
    yandex_client = Yandex(ya_token)
    yandex_client.backup('Backup', os.path.abspath('Photo_Album'))
