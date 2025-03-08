from configparser import ConfigParser


config = ConfigParser()
config.read("config.ini", encoding='utf-8')


TOPICS_URL = config['api'].get('topics_url')
FILE_DOWNLOAD_URL = config['api'].get('file_download_url')

IMAGE_FOLDER = config['File'].get('image_folder')
FILE_FOLDER = config['File'].get('file_folder')


class Group():
    def __init__(self, group_name, group_id, last_dl_time=None):
        self.group_name = group_name  # 星球名称
        self.group_id = int(group_id)  # 星球ID号
        self.last_dl_time = last_dl_time  # 上一次下载数据的时间

    def __str__(self):
        return self.group_name

    def update_last_dl_time(self, last_dl_time):
        self.last_dl_time = last_dl_time
        config = ConfigParser()
        config.read("groups.ini", encoding='utf-8')
        config[str(self.group_id)]['LastDownloadTime'] = last_dl_time
        with open('groups.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    @classmethod
    def load_groups(self):
        config = ConfigParser()
        config.read("groups.ini", encoding='utf-8')
        groups = []

        for section in config.sections():
            if section != 'DEFAULT':
                group = Group(config[section]['GROUP_NAME'],
                              config[section]['GROUP_ID'])
                if 'lastdownloadtime' in config[section].keys():
                    group.last_dl_time = config[section]['lastdownloadtime']
                groups.append(group)
        if len(groups) > 0:
            return groups


def get_headers(file_path='headers.txt'):
    """
    从 header.txt 中读取 headers
    :param file_path: 配置文件路径，默认为 'header.txt'
    :return: 字典格式的 headers
    """
    headers = {}

    try:
        # 打开并读取文件
        with open(file_path, 'r') as file:
            for line in file:
                # 忽略空行和注释行
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 将每行的 key 和 value 按 ':' 分隔并存入字典
                if ':' in line:
                    key, value = line.split(':', 1)  # 只分隔第一次出现的 ':'
                    headers[key.strip()] = value.strip()

    except FileNotFoundError:
        print(f"文件 {file_path} 未找到！")
    except Exception as e:
        print(f"读取文件时发生错误: {e}")

    return headers


GROUPS = Group.load_groups()


if __name__ == '__main__':
    headers = get_headers()
    print(headers)