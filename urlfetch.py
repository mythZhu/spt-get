#!/usr/bin/python -tt
# vim: sw=4 ts=4 sts=4 et ai

import os
import Queue
import urllib
import httplib
import urlparse
import threading
import tempfile

import msger

def _fetch(file_urls, LOOPS=3):
    put_queue = Queue.Queue(0)
    get_queue = Queue.Queue(0)
    for url in file_urls:
        get_queue.put(url, block=False)

    if LOOPS == 1:
        quiet = True 
    else:
        quiet = False

    fetchers = []
    for i in xrange(0, LOOPS):
        fetcher = FetchWorker(get_queue, put_queue, quiet=quiet)
        fetchers.append(fetcher)

    for worker in fetchers:
        worker.setDaemon(True)
        worker.start()
    for worker in fetchers:
        worker.join()

    gains = []
    while True:
        try:
            gains.append(put_queue.get(block=False))
        except Queue.Empty:
            break;

    return gains

def fetch_url(file_url):
    return _fetch([file_url], LOOPS=1)[0]

def fetch_urls(file_urls):
    return _fetch(file_urls, LOOPS=min(len(file_urls), 3))

def check_url(file_url):
    parsed = urlparse.urlsplit(file_url)

    if parsed.port:
        host, port = parsed.netloc.split(':', 2)
    else:
        host = parsed.netloc
        port = 80

    connection = httplib.HTTPConnection(host, port)
    connection.request("HEAD", parsed.path)
    response = connection.getresponse()

    if response.status == 200:
        return True
    else:
        return False

def clean_url():
    urllib.urlcleanup()

class FetchWorker(threading.Thread):
    
    def __init__(self, get_queue, put_queue, quiet=True):
        super(FetchWorker, self).__init__()
        self.__getqueue = get_queue
        self.__putqueue = put_queue
        self.__quiet = quiet

    @staticmethod
    def __show(blocks_read, block_size, total_size):
        pass

    def __fetch(self, task, local_path=None):
        try:
            local_path, msg = urllib.urlretrieve(task, local_path, self.__show)
        except:
            raise IOError("%s is unvalid url" % task)
        else:
            return local_path

    def run(self):
        while True:
            try:
                task = self.__getqueue.get(block=False)
                path = os.path.join(tempfile.gettempdir(), 
                                    os.path.basename(task))
                gain = self.__fetch(task, path)
                if gain:
                    self.__putqueue.put(gain, block=False)
                    self.__quiet or \
                    msger.info("[+] %s" % task)
                else:
                    self.__quiet or \
                    msger.error("[-] %s" % task)
            except Queue.Empty:
                break
