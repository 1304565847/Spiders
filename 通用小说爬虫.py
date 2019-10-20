"""
线程池练手项目，采用多线程爬取小说
作者：楷禅
2019年7月27日
"""


import requests
from lxml import etree
import os
import queue
from threading import Thread, Lock

class Spider():

    def __init__(self, url, name, n=10):
        # url：小说的全部目录界面
        # name：小说名字
        # n：线程数量，默认为10
        self.num = n            #下载线程数量
        self.url = url
        self.error_num = 0      #出错章节数量
        self.novel_name = name 
        self.error_list = []
        self.encode = "utf8"
        # 提取章节列表的规则<a>
        self.list_rule = "//div[@id='list']/dl/dd/a"
        # 提取正文的规则
        self.content_rule = "//div[@id='content']/text()"
        self.content_list = []

    def get_list(self):
        "获取章节列表"
        response = requests.get(self.url)
        # 默认页面编码：gbk
        html = etree.HTML(response.content.decode(self.encode))
        aa = html.xpath(self.list_rule)
        for a in aa:
            title = self.del_title(a.xpath("text()")[0])
            url = "https://www.qu.la/book/162396/"+a.xpath("@href")[0]
            # print(url)
            self.content_list.append({"title": title, "url": url})
    
    def del_title(self, string):
        res = ''
        for i in string:
            index = ord(i)
            # 处理特殊字符
            if 19968 <= index <= 40869 or 97 <= index <= 122 or 65 <= index <= 90 or 48 <= index <= 57 or index == 32:
                res += i
        return res

    def get_content(self, q):
        "从队列中提取章节进行下载"
        # q: 队列
        l = Lock()
        while 1:
            title, url = q.get()
            try:
                response = requests.get(url, timeout=10)
            except:
                # print("超时：", title)
                self.error_num += 1
                self.error_list.append(title+"（网络错误）")
                with open("test.ml", 'a') as ff:
                    ff.write(url+"\n")
            else:
                html = etree.HTML(response.content)
                content = ''.join(html.xpath(self.content_rule))
                # print(content)
                if not os.path.exists("novel"):
                    os.makedirs("novel")
                l.acquire()
                print("已下载："+title)
                l.release()
                # 处理章节名称异常导致的文件错误
                try:
                    with open(os.path.join("novel", f"{title}.txt"), 'w', encoding="utf8") as file:
                        file.write(title+"\n"+str(content)+"\n")
                except:
                    self.error_list.append(title+"(文件名错误)")
                    self.error_num += 1
            finally:
                q.task_done()
        
    def get_novel(self):
        "将单章小说整合成一整部"
        file = open(f"{self.novel_name}.txt", 'w',encoding="utf8")
        for i in self.content_list:
            if i['title'] in self.error_list:
                continue
            try:
                with open(os.path.join("novel", f"{i['title']}.txt"), 'r', encoding="utf8") as f2:
                    file.write(f2.read())
                os.remove(os.path.join("novel", f"{i['title']}.txt"))
            except:
                pass
        file.close()
    
    def run(self):
        print("读取列表中。。。。")
        self.get_list()
        print("列表读取完毕，共%d章" % len(self.content_list))
        q = queue.Queue()
        for i in range(self.num):
            t = Thread(target=self.get_content, args=(q,))
            t.daemon = True
            t.start()
        for i in self.content_list:
            q.put((i['title'], i['url']))
        q.join()
        print("下载完成，文件整合中。。。")
        self.get_novel()
        print("文件整合完毕！！")
        print(f"共计{len(self.content_list)}章，成功下载{len(self.content_list) - self.error_num}章, 失败章节：{'、'.join(self.error_list)}")


a = Spider("https://www.qu.la/book/162396/", "极品公子", 100)
a.run()