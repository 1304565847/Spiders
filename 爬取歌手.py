import requests
import json
import os
from threading import Thread, Lock
from queue import Queue

class Spider():

    def __init__(self, mid, name):
        self.mid = mid
        self.name = name
        self.download_api = "http://211.152.148.26/amobile.music.tc.qq.com/"
        self.api = ["https://u.y.qq.com/cgi-bin/musicu.fcg?-=getUCGI38350760984660526&g_tk=1125629726&loginUin=1791670972&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0&data=%7B%22comm%22%3A%7B%22ct%22%3A24%2C%22cv%22%3A0%7D%2C%22singer%22%3A%7B%22method%22%3A%22get_singer_detail_info%22%2C%22param%22%3A%7B%22sort%22%3A5%2C%22singermid%22%3A%22","","%22%2C%22sin%22%3A","偏移量","%2C%22num%22%3A60%7D%2C%22module%22%3A%22music.web_singer_info_svr%22%7D%7D"]
        self.headers = {
            "Origin": "https://y.qq.com",
            "Referer": "https://y.qq.com/n/yqq/singer/%s.html" % self.mid,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"
        }
        self.music_api = ["http://u.y.qq.com/cgi-bin/musicu.fcg?-=getplaysongvkey2546320457778981&g_tk=1312345255&loginUin=1791670972&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0&data=%7B%22req%22%3A%7B%22module%22%3A%22CDN.SrfCdnDispatchServer%22%2C%22method%22%3A%22GetCdnDispatch%22%2C%22param%22%3A%7B%22guid%22%3A%226543954968%22%2C%22calltype%22%3A0%2C%22userip%22%3A%22%22%7D%7D%2C%22req_0%22%3A%7B%22module%22%3A%22vkey.GetVkeyServer%22%2C%22method%22%3A%22CgiGetVkey%22%2C%22param%22%3A%7B%22guid%22%3A%226543954968%22%2C%22songmid%22%3A%5B%22",'',"%22%5D%2C%22songtype%22%3A%5B0%5D%2C%22uin%22%3A%221791670972%22%2C%22loginflag%22%3A1%2C%22platform%22%3A%2220%22%7D%7D%2C%22comm%22%3A%7B%22uin%22%3A1791670972%2C%22format%22%3A%22json%22%2C%22ct%22%3A24%2C%22cv%22%3A0%7D%7D"]
        self.head = {
            'User-Agent':"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4098.3 Safari/537.36"
            }
        

    def get_musics(self):
        self.api[1] = self.mid
        index = 0
        res = []
        while 1:
            self.api[3] = str(index * 60)
            index += 1
            print("已提取%d页" % index)
            url = "".join(self.api)
            response = requests.get(url, headers=self.headers)
            data = json.loads(response.text)
            # print(data)
            res.extend(data['singer']['data']['songlist'])
            if len(data['singer']['data']['songlist']) <= 55:
                break
        return res
    
    def del_with_data(self, data):
        res = []
        for i in data:
            singer = []
            for j in i['singer']:
                singer.append(j['name'])
            res.append({"name": i['name'], "singers": ",".join(singer), "mid": i['file']['media_mid']})
        return res
    
    def get_vkey(self, mid):
        self.music_api[1] = mid
        data_url = ''.join(self.music_api)
        try:
            data = json.loads(requests.get(data_url, timeout=10).text)
        except:
            # print("网络错误")
            # time.sleep(2)
            return 0
        vkey = data['req']['data']['vkey']
        return vkey
    
    def download(self, queue, num):
        while 1:
            mid, filename = queue.get()
            vkey = self.get_vkey(mid)
            # 判断vkey
            if not vkey:
                print("vkey获取失败", filename)
                queue.task_done()
                continue
            # 拼接URL
            mmid = "C400" + mid + ".m4a"
            # print(vkey)
            download_url = self.download_api + mmid + '?' + 'guid=6543954968&vkey=' + vkey + "&uin=1224&fromtag=6"
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
            if size < 1024:
                print(filename, "未知原因")
                num.put(1)
                queue.task_done()
                continue
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
        print("提取歌曲数据")
        data = self.del_with_data(self.get_musics())
        total = len(data)
        print("数据提取完毕，共%d首歌曲" % total)
        total = len(data)
        print("开始下载")
        tasks = Queue()
        num = Queue()
        for i in range(32):
            t = Thread(target=self.download, args=(tasks, num))
            t.daemon = True
            t.start()
        if not os.path.exists(self.name):
            os.makedirs(self.name)
        # 创建任务
        for i in data:
            # print(i['mid'])
            tasks.put((i['mid'], i['name']))
        tasks.join()
        down_successfully = num.qsize()
        print("成功下载%d首" % down_successfully)
        print("%d首下载失败" % (total - down_successfully))

a = Spider("0025NhlN2yWrP4", "周杰伦")
a.run()