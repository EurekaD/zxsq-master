import requests

url = "https://images.zsxq.com/FsLQqWbFXP9mrGDch1-1McUoDo-y?imageMogr2/auto-orient/quality/100!/ignore-error/1&e=1746028799&s=ytjmyvyyjvmmymt&token=kIxbL07-8jAj8w1n4s9zv64FuZZNEATmlU_Vm6zD:s_6RF9KU0umk8FbHFeUsjXXYERE="  # 替换为你的图片URL
filename = "image.jpg"  # 本地保存的文件名

response = requests.get(url, stream=True)  # 以流的方式下载
if response.status_code == 200:
    with open(filename, "wb") as file:
        for chunk in response.iter_content(1024):  # 每次读取1024字节
            file.write(chunk)
    print("下载完成:", filename)
else:
    print("下载失败:", response.status_code)
