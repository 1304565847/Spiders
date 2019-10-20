import requests
import json
import os
from queue import Queue
from threading import Thread


class Spider():

    def __init__(self, disstid, name):
        "disstid: 歌单id（浏览器地址栏那一串数字） name:歌单名称"
        self.name = name
        self.cdapi = "https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg"
        self.headers = {
            "Origin": "https://y.qq.com",
            "Referer": "https://y.qq.com/n/yqq/playlist/%d.html" % disstid, 
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"
        }
        self.download_api = "http://isure.stream.qqmusic.qq.com/"
        self.music_api = ["http://u.y.qq.com/cgi-bin/musicu.fcg?-=getplaysongvkey2546320457778981&g_tk=1312345255&loginUin=1791670972&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0&data=%7B%22req%22%3A%7B%22module%22%3A%22CDN.SrfCdnDispatchServer%22%2C%22method%22%3A%22GetCdnDispatch%22%2C%22param%22%3A%7B%22guid%22%3A%226543954968%22%2C%22calltype%22%3A0%2C%22userip%22%3A%22%22%7D%7D%2C%22req_0%22%3A%7B%22module%22%3A%22vkey.GetVkeyServer%22%2C%22method%22%3A%22CgiGetVkey%22%2C%22param%22%3A%7B%22guid%22%3A%226543954968%22%2C%22songmid%22%3A%5B%22",'',"%22%5D%2C%22songtype%22%3A%5B0%5D%2C%22uin%22%3A%221791670972%22%2C%22loginflag%22%3A1%2C%22platform%22%3A%2220%22%7D%7D%2C%22comm%22%3A%7B%22uin%22%3A1791670972%2C%22format%22%3A%22json%22%2C%22ct%22%3A24%2C%22cv%22%3A0%7D%7D"]
        self.head = {
            'User-Agent':"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4098.3 Safari/537.36"
            }
        self.cd_params = {
            "type": 1,
            "json": 1,
            "utf8": 1,
            "onlysong": 0,
            "new_format": 1,
            "disstid": disstid,
            "g_tk": 1125629726,
            "loginUin": 1791670972,
            "hostUin": 0,
            "format": "json",
            "inCharset": "utf8",
            "outCharset": "utf-8",
            "notice": 0,
            "platform": "yqq.json",
            "needNewCode": 0
        }
    
    def get_song_list(self):
        response = requests.get(self.cdapi, params=self.cd_params, headers = self.headers)
        res = []
        data = json.loads(response.text)
        for i in data['cdlist'][0]['songlist']:
            singer = []
            for j in i['singer']:
                singer.append(j['name'])
            res.append({"name": i['name'], "singers": ','.join(singer), "mid": i['mid']})
        return res
    
    def get_vkey(self, mid):
        headers = {
            "Referer": "https://y.qq.com/qqmusic/player_detail.html",
            "Sec-Fetch-Mode": "no-cors",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"
        }
        self.music_api[1] = mid#"002E3MtF0IAMMY"
        data_url = ''.join(self.music_api)
        try:
            data = json.loads(requests.get(data_url, headers=headers).text)
        except:
            print("网络错误")
            # time.sleep(2)
            return 0
        vkey = data['req']['data']['vkey']
        filename = data['req_0']['data']['midurlinfo'][0]['filename']
        # print(vkey)
        # exit(0)
        self.download_api = data['req_0']['data']['sip'][1]
        return vkey, filename
    
    def download(self, queue, num):
        while 1:
            mid, filename = queue.get()
            vkey,mmid = self.get_vkey(mid)
            # 判断vkey
            if not vkey:
                print("vkey获取失败", filename)
                queue.task_done()
                continue
            # 拼接URL
            # mmid = "C400" + mid + ".m4a"
            download_url = self.download_api + mmid + '?' + 'guid=6543954968&vkey=' + vkey + "&uin=0&fromtag=98"
            # print(download_url)
            # 验证歌曲名称有效性
            try:
                data = requests.get(download_url, headers=self.head, timeout=10).content
            except:
                print("连接超时")
                queue.task_done()
                # time.sleep(1)
                continue
            
            size = len(data)
            
            try:
                with open(os.path.join(self.name, "%s.m4a" % filename), 'wb+') as f:
                    f.write(data)
            except:
                print("歌曲名称含有非法字符：%s" % filename)
                # continue
            else:
                print("已下载：%s    %dk " % (filename, (size / 1024)))
                num.put(1)
            finally:
                # 释放队列元素
                queue.task_done()
            
        
    def run(self):
        print("提取歌单数据。。。")
        tasks = Queue()
        num = Queue()
        # 下载线程的数量
        for i in range(15):
            t = Thread(target=self.download, args=(tasks, num))
            t.daemon = True
            t.start()
        data = self.get_song_list()
        total = len(data)
        print("歌单数据提取完毕，共%d首歌曲" % total)
        print("开始下载")
        # 创建歌单文件夹
        if not os.path.exists(self.name):
            os.makedirs(self.name)
        # 创建任务
        for i in data:
            tasks.put((i['mid'], i['name']))

        tasks.join()
        down_successfully = num.qsize()
        print("成功下载%d首" % down_successfully)
        print("%d首下载失败" % (total - down_successfully))


a = Spider(2670477537, "元气少女郭德纲")
a.run()