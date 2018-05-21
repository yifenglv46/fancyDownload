# coding: utf-8

__author__='https://cpp.la'

import requests
import time
import sys
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
        # todo: chunked编码方案预留
        pass


if __name__ == '__main__':
    '''
    python fancyDownload.py $fileUrl $filePath
    '''
    if len(sys.argv) != 3:
        raise Exception("Parameter Exception!")
    fileUrl = sys.argv[1]
    filePath = sys.argv[2]

    startTime = time.time()
    getFileWork(fileUrl, filePath)
    endTime = time.time()
    print("总耗时: %ds, 平均速度: %0.2fMb/s" % (int(endTime-startTime), _OBJECT_FILE_SIZE/1024/1024/(endTime-startTime)))