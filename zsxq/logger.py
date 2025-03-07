"""
使用单例模式设计的日志对象获取函数，
logging 模块是线程安全的
"""

import logging
import os
from datetime import datetime
from functools import lru_cache
import gzip
from logging.handlers import TimedRotatingFileHandler

LOGFILE = ""


@lru_cache()
def get_logger(log_name="sync"):
    """
    使用 lru_cache 装饰器后，如果不传参，将返回同一个日志对象。
    :param log_name: 日志名称前缀，默认为 sync
    :return:
    """

    logger = logging.getLogger(__name__)

    log_file = '{}-{}.logs'.format(log_name, datetime.now().strftime('%Y%m%d_%H%M%S'))
    print(log_file)
    global LOGFILE
    LOGFILE = log_file

    log_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs', log_file))

    logging.basicConfig(filename=log_file_path, level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d [%(levelname)s]  %(message)s',
                        datefmt='## %Y-%m-%d %H:%M:%S',
                        encoding='utf-8')
    return logger


def close_logger():
    """
    关闭日志文件句柄。
    """
    logger = get_logger()
    while logger.handlers:
        handler = logger.handlers[0]
        handler.close()
        logger.removeHandler(handler)


@lru_cache()
def get_logger_daily(log_name="sync"):
    """
    创建按日期分割的日志文件，前一天的日志将自动压缩。
    :param log_name: 日志名称前缀，默认为 sync
    :return: logger 对象
    """
    logger = logging.getLogger(log_name)
    if logger.hasHandlers():
        return logger  # 避免重复添加 Handler

    logger.setLevel(logging.INFO)

    # 日志文件路径
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{log_name}.log")

    # 设置按日期切分日志
    handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    handler.suffix = "%Y-%m-%d"  # 设置日志文件后缀
    handler.extMatch = r"^\d{4}-\d{2}-\d{2}$"  # 匹配日期后缀的正则

    # 日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d [%(levelname)s]  %(message)s',
        datefmt='## %Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)


def compress_log_file(log_file, current_date=datetime.now().strftime('%Y-%m-%d')):
    """
    压缩日志文件
    这是用来压缩日志文件的方法， 根据文件的大小， 来自前同事 wx,我稍加优化
    如果文件为空，删除这个日志文件
    这里存在的局限性是：仅仅通过日志的文件大小来决定压缩与否，根据日期来开启日志（例如每天一个日志文件）
    :param current_date: 当前的日期，用来给压缩的日志文件命名
    :param log_file: 当前的日志文件的路径，如果该文件大小达到阈值将被压缩并直接删除该日志。因此运行此方法后不能再写日志，除非再获取一个日志对象
    :return:
    """
    log_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', log_file))
    print(log_file_path)
    if os.path.exists(log_file_path):
        if os.path.getsize(log_file_path) > 40960:  # 文件大小阈值为 40 KB
            print(f"压缩日志文件：{log_file_path}")
            # 读取原文件内容，直接写入压缩文件
            with open(log_file_path, 'rb') as f_in:
                compressed_data = gzip.compress(f_in.read())
            # 将压缩后的数据写入新的 .gz 文件
            compressed_file_path = f"{log_file_path}.{current_date}.gz"
            with open(compressed_file_path, 'wb') as f_out:
                f_out.write(compressed_data)
            # 删除原文件
            os.remove(log_file_path)
            print(f"压缩完成并删除原文件：{log_file_path}")

