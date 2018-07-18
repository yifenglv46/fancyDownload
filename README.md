# fancyDownload
Linux多线程下载工具，python多线程下载（支持youtube, onedrive），  "IDM" on linux

# 依赖
sudo pip install -r requirements.txt

# 帮助
```bash
python fancyDownload.py $fileUrl $filePath

# $fileurl: 文件链接    
# $filePath: 完整存储路径
    
# eg1: python fancyDownload.py https://xxx.com/1.zip ~/1.zip
# eg2: python fancyDownload.py https://www.youtube.com/watch?v=z5d1LYRC-PA /download/jiayuan.mp4
# eg3: python fancyDownload.py onedrive/myvideo/taohua.mkv ~/taohua.mkv
```

# 说明
20180718: version1.2 加入多线程下载onedrive (格式: onedrive/$待下载的文件onedrive绝对路径)   
20180613: version1.1 加入多线程下载youtube    
20180518: version1.0 支持http,https协议多线程下载    
demo: https://cpp.la/162.html

# 未完待续
