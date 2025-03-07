import requests
import config
from logger import get_logger
import time
import pandas as pd
from requests import RequestException
from urllib.parse import quote
import json
from datetime import datetime

log = get_logger("zsxq")

file_path = r"zsxq.xlsx"

df = pd.read_excel(file_path)


def save(topics):
    earliest_time = ""
    for topic in topics:
        type = topic['type']
        earliest_time = topic['create_time']

        if 'talk' in topic:
            row = {
                'topic_id': topic['topic_id'],
                'author': topic['talk']['owner']['name'],
                'title': topic['title'],
                'date': topic['create_time'],
                'content': topic['talk']['text'],
                # 'file': topic['talk']['files'] if 'files' in topic['talk'] else [],
                'images': [image['original']['url'] if 'original' in image else None for image in
                           topic['talk']['images']]
                if 'images' in topic['talk'] else []
            }
            df.loc[len(df)] = row
    return earliest_time


def process_topics(url, last_download_time):
    try:
        topics_page = requests.get(url, headers=config.get_headers())
        earliest_time = None
        if topics_page.status_code == 200:
            topics = json.loads(topics_page.text).get('resp_data').get('topics')
            earliest_time = save(topics)

        t1 = datetime.strptime(earliest_time, "%Y-%m-%dT%H:%M:%S.%f%z")  # 抓取的最早时间
        t2 = datetime.strptime(last_download_time, "%Y-%m-%dT%H:%M:%S.%f%z")  # 上次抓取的时间
        if t1 > t2:
            return earliest_time
        else:
            return None

    except RequestException as e:
        print('Get topics error.', e.args)

        return None


def get_topic_list(base_url, last_download_time, earliest_time=None):
    if earliest_time:
        url = base_url + '&end_time=' + quote(earliest_time)
    else:
        url = base_url

    create_time = process_topics(url, last_download_time)

    time.sleep(5)
    if create_time:
        print('Got topics till ', create_time)
        get_topic_list(base_url, last_download_time, create_time)


def start():
    for group in config.GROUPS:
        last_download_time = group.last_dl_time
        base_url = config.TOPICS_URL.format(group.group_id)
        get_topic_list(base_url, last_download_time)

    df.to_excel(file_path, index=False)


if __name__ == '__main__':
    start()
