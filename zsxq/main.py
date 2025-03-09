import random

import requests
import config
from logger import get_logger
import time
import pandas as pd
from requests import RequestException
from urllib.parse import quote, urlparse
import json
from datetime import datetime
import os

log = get_logger("zsxq")

# 获取图片和文件存储根目录
IMAGE_ROOT = config.IMAGE_FOLDER
FILE_ROOT = config.FILE_FOLDER


def download_file(file_id, file_name, group_name, topic_id, index):
    """下载文件并保存到指定目录"""
    try:
        # 创建保存目录，使用配置的根目录
        save_dir = os.path.join(FILE_ROOT, group_name, str(topic_id))
        os.makedirs(save_dir, exist_ok=True)

        # 获取文件扩展名
        file_ext = os.path.splitext(file_name)[1]
        if not file_ext:
            file_ext = '.unknown'

        # 构建保存路径
        save_path = os.path.join(save_dir, f"{index}_{file_name}")
        
        # 如果文件已存在，直接返回路径
        if os.path.exists(save_path):
            return save_path

        # 先获取文件的下载链接
        url = config.FILE_DOWNLOAD_URL.format(file_id)
        response = requests.get(url, headers=config.get_headers())
        
        if response.status_code == 200:
            download_url = json.loads(response.text).get('resp_data', {}).get('download_url')
            if download_url:
                # 使用流式下载文件
                file_response = requests.get(download_url, stream=True)
                if file_response.status_code == 200:
                    with open(save_path, 'wb') as file:
                        for chunk in file_response.iter_content(1024):  # 每次读取1024字节
                            file.write(chunk)
                    log.info(f"Downloaded file: {save_path}")
                    return save_path
                else:
                    log.error(f"Failed to download file from {download_url}, status code: {file_response.status_code}")
            else:
                log.error(f"No download URL found in response: {response.text}")
        else:
            log.error(f"Failed to get download URL, status code: {response.status_code}")
        return None
    except Exception as e:
        log.error(f"Error downloading file {file_id}: {str(e)}")
        return None


def download_image(url, group_name, topic_id, index):
    """下载图片并保存到指定目录"""
    try:
        # 创建保存目录，使用配置的根目录
        save_dir = os.path.join(IMAGE_ROOT, group_name, str(topic_id))
        os.makedirs(save_dir, exist_ok=True)

        # 从URL中获取文件扩展名
        parsed_url = urlparse(url)
        file_ext = os.path.splitext(parsed_url.path)[1]
        if not file_ext:
            file_ext = '.jpg'  # 默认扩展名

        # 构建保存路径
        save_path = os.path.join(save_dir, f"{index}{file_ext}")
        
        # 如果文件已存在，直接返回相对路径
        if os.path.exists(save_path):
            return save_path

        # 使用流式下载图片
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):  # 每次读取1024字节
                    file.write(chunk)
            log.info(f"Downloaded image: {save_path}")
            return save_path
        else:
            log.error(f"Failed to download image {url}, status code: {response.status_code}")
            return None
    except Exception as e:
        log.error(f"Error downloading image {url}: {str(e)}")
        return None


def save(topics, df, group_name):
    earliest_time = ""
    count = 0
    for topic in topics:
        type = topic['type']
        earliest_time = topic['create_time']

        if 'talk' in topic:
            # 下载图片
            image_paths = []
            if 'images' in topic['talk']:
                for i, image in enumerate(topic['talk']['images']):
                    image_url = image['original']['url'] if 'original' in image else None
                    if image_url:
                        saved_path = download_image(image_url, group_name, topic['topic_id'], i)
                        if saved_path:
                            image_paths.append(saved_path)

            # 下载文件
            file_paths = []
            if 'files' in topic['talk']:
                for i, file in enumerate(topic['talk']['files']):
                    file_id = file.get('file_id')
                    file_name = file.get('name')
                    if file_id and file_name:
                        saved_path = download_file(file_id, file_name, group_name, topic['topic_id'], i)
                        if saved_path:
                            file_paths.append(saved_path)

            row = {
                'topic_id': topic['topic_id'],
                'author': topic['talk']['owner']['name'],
                'title': topic['title'],
                'date': topic['create_time'],
                'content': topic['talk']['text'],
                'images': ','.join(image_paths) if image_paths else '',  # 将图片路径数组转换为逗号分隔的字符串
                'files': ','.join(file_paths) if file_paths else ''  # 将文件路径数组转换为逗号分隔的字符串
            }
            df.loc[len(df)] = row
            count += 1
    log.info(f"Saved {count} new topics, earliest time: {earliest_time}")
    return earliest_time


def parse_time(time_str):
    try:
        # 先尝试带时区的格式
        dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        # 转换为不带时区的时间
        return dt.replace(tzinfo=None)
    except ValueError:
        try:
            # 如果失败，尝试不带时区的格式
            return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            # 如果还失败，可能没有微秒部分
            return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")


def process_topics(url, last_download_time, df, group_name):
    retry_count = 0
    while retry_count < 3:
        try:
            log.info(f"Fetching topics from URL: {url}")
            topics_page = requests.get(url, headers=config.get_headers())
            earliest_time = None
            if topics_page.status_code == 200:
                response_data = json.loads(topics_page.text)
                topics = response_data.get('resp_data', {}).get('topics', [])
                if topics:
                    earliest_time = save(topics, df, group_name)
                    t1 = parse_time(earliest_time)  # 抓取的最早时间
                    t2 = parse_time(last_download_time)  # 上次抓取的时间

                    if t1 > t2:
                        # 本次抓取的最早的内容的时间 晚于（大于） 上次抓取的时间， 继续抓取
                        return earliest_time
                    else:
                        log.info("Reached last download time, stopping fetch")
                        return None
                else:
                    log.warning(f"No topics found in response: {response_data}")
                    retry_count += 1
                    if retry_count < 3:
                        log.info(f"Retrying request (attempt {retry_count}/3)")
                        random_sleep()
                    continue
            else:
                log.error(f"Failed to fetch topics from {url}, status code: {topics_page.status_code}")
                return None

        except RequestException as e:
            log.error(f'Get topics error: {str(e)}')
            return None
        except Exception as e:
            log.error(f'Unexpected error while processing topics: {str(e)}')
            log.error(f'earliest_time: {earliest_time}')
            log.error(f'last_download_time: {last_download_time}')
            return None
    
    log.error("Max retry attempts reached, giving up")
    return None


# 随机延时
def random_sleep():
    # 随机延时3-8秒
    delay = random.uniform(10, 20)
    log.info(f"Random sleep {delay} seconds")
    time.sleep(delay)


def get_topic_list(base_url, last_download_time, df, group_name):
    end_time = None
    while True:
        url = base_url
        if end_time:
            url = base_url + '&end_time=' + quote(end_time)
        
        end_time = process_topics(url, last_download_time, df, group_name)
        if not end_time:
            break
            
        random_sleep()
        log.info(f'Got topics till {end_time}, continuing to fetch earlier topics')


def start():
    log.info("Starting data fetch process")
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")  # 移除时区信息
    
    # 确保图片和文件根目录存在
    os.makedirs(IMAGE_ROOT, exist_ok=True)
    os.makedirs(FILE_ROOT, exist_ok=True)
    log.info(f"Using image root directory: {IMAGE_ROOT}")
    log.info(f"Using file root directory: {FILE_ROOT}")
    
    for group in config.GROUPS:
        log.info(f"Processing group: {group.group_name} (ID: {group.group_id})")
        file_path = r"zsxq-{}.xlsx".format(group.group_name)

        # Create new DataFrame if file doesn't exist, otherwise read existing file
        if os.path.exists(file_path):
            log.info(f"Reading existing file: {file_path}")
            df = pd.read_excel(file_path)
            log.info(f"Found {len(df)} existing records")
        else:
            log.info(f"Creating new file: {file_path}")
            df = pd.DataFrame(columns=['topic_id', 'author', 'title', 'date', 'content', 'images', 'files'])
        
        last_download_time = group.last_dl_time
        base_url = config.TOPICS_URL.format(group.group_id)
        log.info(f"Starting fetch from last download time: {last_download_time}")
        get_topic_list(base_url, last_download_time, df, group.group_name)
        
        # Update the last download time for this group
        group.update_last_dl_time(current_time)
        log.info(f"Updated last download time to: {current_time}")

        df.to_excel(file_path, index=False)
        log.info(f"Saved {len(df)} total records to {file_path}")

    log.info("Completed data fetch process for all groups")


if __name__ == '__main__':
    start()
