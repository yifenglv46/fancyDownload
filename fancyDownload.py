#!/usr/bin/env python
# coding: utf-8

__author__='https://cpp.la'

import requests
import time
import sys
import re
import os
import threading
import onedrivesdk
import pickle

MAX_THREAD = 10
SPLIT_SIZE = 1024*1024*32

def getFileThread(objectFileUrl, objectFilePath, objectSession, singleChunk):
    '''

    :param objectFileUrl: 请求链接
    :param objectFilePath: 目标存储路径
    :param objectSession: 验证头
    :param singleChunk: 切块
    :return:
    '''
    fileStart = (singleChunk-1)*SPLIT_SIZE
    fileEnd = fileStart + SPLIT_SIZE - 1

    headers = objectSession
    headers["User-Agent"] = "Mozilla/5.0 (compatible; fancyDownload/1.1; +https://github.com/cppla/fancyDownload)"
    headers["Range"] = "bytes=%d-%d" % (fileStart, fileEnd)

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
        f.write(r.content)

def getFileWork(objectFileUrl, objectFilePath, objectSession):
    '''

    :param objectFileUrl: 请求链接
    :param objectFilePath: 目标存储路径
    :param objectSession: 验证头
    :return:
    '''
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
                        'objectSession': objectSession,
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
        headers = objectSession
        headers["User-Agent"] = "Mozilla/5.0 (compatible; fancyDownload/1.1; +https://github.com/cppla/fancyDownload)"

        r = requests.get(
            url=objectFileUrl,
            headers=headers,
            stream=True
        )
        with open(objectFilePath, "wb+") as f:
            for chunk in r.iter_content(chunk_size=SPLIT_SIZE):
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

def getOnedrive(fileUrl, filePath):
    '''
    :param fileUrl:
    :param filePath:
    :return:
    '''

    from onedrivesdk import HttpProvider
    from onedrivesdk.http_response import HttpResponse
    class HttpProviderByFCD(HttpProvider):

        def __init__(self):
            super(HttpProviderByFCD, self).__init__()

        def download(self, headers, url, path):

            response = requests.head(url, headers=headers)
            if response.status_code in [301, 302]:
                response = requests.head(response.headers['Location'], headers=headers)

            if response.status_code == 200:
                getFileWork(response.url, path, headers)
                custom_response = HttpResponse(response.status_code, response.headers, None)
            else:
                custom_response = HttpResponse(response.status_code, response.headers, response.text)

            return custom_response

    # save key to file
    if os.path.exists(".fancyDownloadKey") is False:
        print(u'第一次使用请创建应用, 创建教程: https://cpp.la/xx.html')
        redirect_uri = raw_input("请输入应用回调链接: ")
        client_id = raw_input('请输入应用ID: ')
        client_secret = raw_input("请输入应用密钥: ")
        api_base_url = 'https://api.onedrive.com/v1.0/'
        scopes = ['wl.signin', 'wl.offline_access', 'onedrive.readwrite']
        xdict = {
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret,
            'api_base_url': api_base_url,
            'scopes': scopes
        }
        with open('.fancyDownloadKey', 'wb') as f:
            pickle.dump(xdict, f)
    else:
        with open('.fancyDownloadKey', 'rb') as f:
            xdict = pickle.load(f)
        redirect_uri = xdict["redirect_uri"]
        client_id = xdict["client_id"]
        client_secret = xdict["client_secret"]
        api_base_url = xdict["api_base_url"]
        scopes = xdict["scopes"]

    # save session to file
    if os.path.exists(".fancyDownloadSession") is False:
        http_provider = HttpProviderByFCD()
        auth_provider = onedrivesdk.AuthProvider(
            http_provider=http_provider,
            client_id=client_id,
            scopes=scopes)

        client = onedrivesdk.OneDriveClient(api_base_url, auth_provider, http_provider)
        auth_url = client.auth_provider.get_auth_url(redirect_uri)

        print('****************************************')
        print(u'一. 复制URL到浏览器-->回车-->点击是')
        print(u'二. 复制"操作一"浏览器跳转后链接"code="后边的字符串.')
        print(u"URL: %s" % auth_url)
        code = raw_input('请输入code代码: ')
        # client.auth_provider.authenticate(code, redirect_uri, client_secret)

        auth_provider = onedrivesdk.AuthProvider(http_provider,
                                                 client_id,
                                                 scopes)
        auth_provider.authenticate(code, redirect_uri, client_secret)
        dotfancyDownload = auth_provider.save_session()
        with open('.fancyDownloadSession', 'wb') as f:
            pickle.dump(dotfancyDownload, f)
    else:
        with open('.fancyDownloadSession', 'rb') as f:
            dotfancyDownload = pickle.load(f)
        http_provider = HttpProviderByFCD()

    # start download file
    dotfancyDownload = onedrivesdk.AuthProvider(http_provider,
                                             client_id,
                                             scopes)
    dotfancyDownload.load_session()
    dotfancyDownload.refresh_token()
    fcdClient = onedrivesdk.OneDriveClient(api_base_url, dotfancyDownload, http_provider)

    root_folder = fcdClient.item(drive='me', id='root').children["%s" % fileUrl.split("onedrive/")[-1]].get()
    id_of_file = root_folder.id
    fcdClient.item(drive='me', id=id_of_file).download(filePath)


if __name__ == '__main__':
    '''
    python fancyDownload.py $fileUrl $filePath
    '''
    if len(sys.argv) != 3:
        raise Exception("Parameter Exception!")
    fileUrl = sys.argv[1]
    filePath = sys.argv[2]

    if 'https://www.youtube.com' in fileUrl:
        getYoutube(fileUrl, filePath)
    elif 'onedrive' in fileUrl:
        getOnedrive(fileUrl, filePath)
    else:
        getFileWork(fileUrl, filePath, {})