import requests
import json
from threading import Thread, Lock
import random
import time
from queue import Queue


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36",
    "Cookie": "SINAGLOBAL=4694052605580.892.1539224802208; _ga=GA1.2.367985509.1563892247; __gads=ID=046b4374836fcaf2:T=1563892255:S=ALNI_MaxqZloB2y3r48acs4r-pVbDH0I_w; UOR=gl.ali213.net,widget.weibo.com,www.baidu.com; un=15009278915; wvr=6; Ugrow-G0=e1a5a1aae05361d646241e28c550f987; login_sid_t=ebde4b427434e5640f1a5da3e3bff514; cross_origin_proto=SSL; YF-V5-G0=8a1a69dc6ba21f1cd10b039dff0f4381; WBStorage=edfd723f2928ec64|undefined; _s_tentry=passport.weibo.com; wb_view_log=1536*8641.25; Apache=3397907221541.283.1564663147959; ULV=1564663147965:32:1:1:3397907221541.283.1564663147959:1564070441500; WBtopGlobal_register_version=307744aa77dd5677; crossidccode=CODE-yf-1HTamD-IRgUI-0o68pgK68PYeClpdf661a; SCF=Amhqv2bWYScsd-yDOzUDVLu_VbZBV-KNXDdnzAQ1-5Y4LZYbYgrnC-ASdH2j0mN1zXUTL6k1LmBaDfxVRT1p39E.; SUB=_2A25wRq34DeRhGeBO6lUV9yfEzTqIHXVTNZgwrDV8PUNbmtAKLXWnkW9NReVMbWq5YqHLfWzT097zrugNPkVf-Dx6; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W56pMGFVnw9rYgc-4KQvLVW5JpX5K2hUgL.Foq7eKMXS0.RSoq2dJLoIpzLxKqLBK-LBoMLxKMLBKqL1h-t; SUHB=0ebt-iDsxO4U5Q; ALF=1565268008; SSOLoginState=1564663208; wb_view_log_6017479866=1536*8641.25; webim_unReadCount=%7B%22time%22%3A1564663218704%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22allcountNum%22%3A34%2C%22msgbox%22%3A0%7D; YF-Page-G0=89906ffc3e521323122dac5d52f3e959|1564663218|1564663213"
}

with open("ip.json", "r") as f:
    data = json.loads(f.read())
proxy = []
for i in data:
    proxy.append({"http": f"http://{i['ip']}:{i['port']}" })


index = 0
def run(l, q):
    while 1:
        q.get()
        time.sleep(1)
        global index
        try:
            reponse = requests.get("https://weibo.com/u/7251910321?refer_flag=1001030103_", proxies=random.choice(proxy) ,headers=headers, timeout=5)
        except:
            q.task_done()
            continue
        if reponse.status_code == 414:
            time.sleep(60)
        l.acquire()
        index += 1
        print(index)
        l.release()
        q.task_done()

l = Lock()
q = Queue()
# 线程数量
for i in range(300):
    t = Thread(target=run, args=(l, q))
    t.daemon = True
    t.start()


# 总数量
for i in range(2000):
    q.put(1)

q.join()