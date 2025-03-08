# 知识星球数据抓取

# headers.txt
该文件最为关键，用于存放cookies和其它header里的内容,没有正确的cookies自然不能下载数据。
首先在网页中登录知识星球，然后直接从Network中找到对应的Request，再将Request Hearder复制过来就可以。

# group.ini
用于记录每个星球上次下载的时间，避免重复下载数据。

# Zsxq.ini
用于配置知识星球的各种URL，其中版本号更新得会快一些。
DOWNLOAD_FILE_FLAG用于配置是否在下载文章的同时下载对应的文件（如果有的话）。








