# coding: utf-8

__author__='https://cpp.la'

import requests
import time
import sys
import re
import threading

# 省内存模式还是暴力下载模式, 默认暴力下载
OPEN_FORCE = 1
MAX_THREAD = 10
SPLIT_SIZE = 1024*1024*32
_OBJECT_FILE_SIZE = 0

def getFileThread(objectFileUrl, objectFilePath, singleChunk):
    fileStart = (singleChunk-1)*SPLIT_SIZE
    fileEnd = fileStart + SPLIT_SIZE - 1
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; fancyDownload/1.0; +https://github.com/cppla/fancyDownload)',
        'Range': 'bytes=%d-%d' % (fileStart, fileEnd)
    }
    r = requests.get(
        url=objectFileUrl,
        headers=headers,
        stream=True
    )
    # http code: 4xx, 5xx
    if str(r.status_code)[0] in ['4', '5']:
        time.sleep(2)
        r = requests.get(
            url=objectFileUrl,
            headers=headers,
            stream=True
        )
    with open(objectFilePath, "rb+") as f:
        f.seek((singleChunk - 1) * SPLIT_SIZE)
        if OPEN_FORCE:
            f.write(r.content)
        else:
            for chunk in r.iter_content(chunk_size=512):
                if chunk:
                    f.write(chunk)

def getFileWork(objectFileUrl, objectFilePath):
    r = requests.head(objectFileUrl)
    if r.status_code in [301, 302]:
        r = requests.head(r.headers['Location'])

    if r.status_code in [404, 501, 502, 503]:
        print(u'服务器异常,返回码: %d' % r.status_code)
        return
    elif r.status_code in [401]:
        print(u'服务器需要鉴权,返回码: %d' % r.status_code)
        return

    if 'Content-Length' in r.headers:
        objectFileSize = int(r.headers['Content-Length'])
        global _OBJECT_FILE_SIZE
        _OBJECT_FILE_SIZE = objectFileSize

        with open(objectFilePath, "wb") as f:
            f.truncate(objectFileSize)

        splitCount = int(objectFileSize/SPLIT_SIZE) + 1
        while splitCount:
            if threading.activeCount() < MAX_THREAD:
                t = threading.Thread(
                    target=getFileThread,
                    kwargs={
                        'objectFileUrl': objectFileUrl,
                        'objectFilePath': objectFilePath,
                        'singleChunk': splitCount
                    }
                )
                splitCount = splitCount - 1
                t.setDaemon(True)
                t.start()
            else:
                time.sleep(0.1)
        currentThread = threading.currentThread()
        for t in threading.enumerate():
            if t is currentThread:
                continue
            else:
                t.join()
    else:
        # beta 1.0 for chunked
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; fancyDownload/1.0; +https://github.com/cppla/fancyDownload)'
        }
        r = requests.get(
            url=objectFileUrl,
            headers=headers,
            stream=True
        )
        with open(objectFilePath, "wb+") as f:
            for chunk in r.iter_content(chunk_size=SPLIT_SIZE):
                _OBJECT_FILE_SIZE += (len(chunk))
                if chunk:
                    f.write(chunk)

def getYoutube(objectFileUrl, objectFilePath):
    '''
    Now get source from www.clipconverter.cc
    :param objectFileUrl:
    :param objectFilePath:
    :return:
    '''
    r = requests.post(
        url='https://www.clipconverter.cc/check.php',
        data={
            'mediaurl': '%s' % objectFileUrl
        }
    )
    if r.status_code != 200:
        print(u'资源解析失败,返回码: %d' % r.status_code)
        return
    else:
        jsonValue = r.json()
        if 'url' not in jsonValue:
            print(u'ip异常,需Youtube验证码验证!')
            return

        print('%s' % '*'*50)
        for i_index, i in enumerate(jsonValue["url"]):
            desc_html = i["text"]
            filetype = i["filetype"]
            re_flag = re.compile(r'<[^>]*>', re.S)
            desc_str = re_flag.sub('', desc_html)
            print(" %d: %s, %s" % (i_index+1, desc_str.replace('YouTube Video ',''), filetype))
        print('%s' % '*' * 50)
        videoVersion = input('视频序号(3GP冷存储,慎选! 视频源越热门下载速度越快: 1080p > 720p > 360p):')

        videoInfo = jsonValue["url"][videoVersion-1]

        objectFileUrl = videoInfo["url"]
        objectFilePath = objectFilePath.split('.')[0] + '_' + videoInfo["text"].split('(')[1].split(')')[0] + '.' + objectFilePath.split('.')[-1]
        objectFilePath = objectFilePath.replace(objectFilePath.split('.')[-1], videoInfo["filetype"].lower())
        print(u'校验后的存储路径: %s' % objectFilePath)
        getFileWork(objectFileUrl, objectFilePath)

if __name__ == '__main__':
    '''
    python fancyDownload.py $fileUrl $filePath
    '''
    if len(sys.argv) != 3:
        raise Exception("Parameter Exception!")
    fileUrl = sys.argv[1]
    filePath = sys.argv[2]

    startTime = time.time()
    if 'https://www.youtube.com' in fileUrl:
        getYoutube(fileUrl, filePath)
    else:
        getFileWork(fileUrl, filePath)
    endTime = time.time()
    print(u"总耗时: %ds, 平均速度: %0.2fMb/s" % (int(endTime-startTime), _OBJECT_FILE_SIZE/1024/1024/(endTime-startTime)))