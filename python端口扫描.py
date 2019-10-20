import socket
from threading import Thread, Lock
from queue import Queue
import time

l = Lock()
HOST = "127.0.0.1"

def get_port(q):
    global l
    while 1:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = q.get()
        ADDR = (HOST, port)
        res = s.connect_ex(ADDR)
        if not res: 
            l.acquire()
            print("端口开放：", port)
            l.release()
        q.task_done()

q = Queue()
for i in range(6000):
    t = Thread(target=get_port, args=(q, ))
    t.daemon = True
    t.start()

for i in range(1,65536):
    q.put(i)

a = time.time()
q.join()
print(time.time() - a)