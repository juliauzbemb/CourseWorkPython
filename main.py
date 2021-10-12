import requests
from pprint import pprint
import json
import os
import datetime
import PySimpleGUI as sg
import time


def time_convert(time_unix):
    time_bc = datetime.datetime.fromtimestamp(time_unix)
    str_time = time_bc.strftime('%Y-%m-%d time %H-%M-%S')
    return str_time


class VkPhotoOwner:
    url = 'https://api.vk.com/method/'

    def __init__(self, owner_id):
        with open('Vktoken.txt', 'r') as file:
            token = file.read().strip()
        self.params = {
            'access_token': token,
            'v': '5.131',
            'owner_id': owner_id
        }

    def get_vk_photos(self):
        get_photos_url = self.url + 'photos.get'
        get_photos_params = {
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1,
            'count': 1000
        }
        req = requests.get(get_photos_url, params={**self.params, **get_photos_params}).json()['response']['items']
        return req

    def get_photo_dict(self):
        photos = self.get_vk_photos()
        photo_dict = {}
        for photo in photos:
            max_size_type = photo["sizes"][-1]["type"]
            photo_url = photo["sizes"][-1]["url"]
            likes_count = photo["likes"]["count"]
            photo_date = time_convert(photo["date"])
            value = photo_dict.get(likes_count, [])
            value.append({'date': photo_date, 'url': photo_url, 'size': max_size_type})
            photo_dict[likes_count] = value
        return photo_dict

    def get_json_file(self):
        json_list = []
        list_for_download = []
        photo_dict = self.get_photo_dict()
        for item in photo_dict.keys():
            for value in photo_dict[item]:
                if len(photo_dict[item]) == 1:
                    file_name = f'{item}.jpeg'
                else:
                    file_name = f'{item} {value["date"]}.jpeg'
                json_list.append({'file_name': file_name, 'size': value['size']})
                list_for_download.append({'file_name': file_name, 'url': value['url']})
        with open('json_file', 'w') as json_file:
            json.dump(json_list, json_file, indent=2, ensure_ascii=False)
        return json_list, list_for_download

    def download_photos(self):
        json_list, list_for_download = self.get_json_file()
        os.mkdir('Photo_Album')
        for element in list_for_download:
            with open(f'Photo_Album/{element["file_name"]}', 'bw') as file:
                resp_download = requests.get(element["url"], stream=True)
                for chunk in resp_download.iter_content(4096):
                    file.write(chunk)


with open('Yatoken.txt') as file_obj:
    token = file_obj.read().strip()


class Yandex:
    def __init__(self, token):
        self.token = token
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources'

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'OAuth {self.token}'
        }

    def create_folder(self, path):
        headers = self.get_headers()
        requests.put(f'{self.url}?path={path}', headers=headers)

    def upload_file(self, loadfile, savefile, replace=False):
        headers = self.get_headers()
        res = requests.get(f'{self.url}/upload?path={savefile}&overwrite={replace}', headers=headers).json()
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
                sg.one_line_progress_meter('Процесс загрузки файлов', i + 1, len(files), '-key-')
                time.sleep(1)


if __name__ == "__main__":
    vk_photo = VkPhotoOwner('552934290')
    # pprint(vk_photo.get_vk_photos())
    # pprint(vk_photo.get_photo_dict())
    # pprint(vk_photo.get_json_file())
    # vk_photo.download_photos()
    yandex_client = Yandex(token)
    yandex_client.backup('Backup', os.path.abspath('Photo_Album'))
