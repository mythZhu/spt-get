#!/usr/bin/python -tt
# vim: sw=4 ts=4 sts=4 et ai

import os
import Queue
import shutil
import threading

import msger

def install_pkgs(file_paths, rootdir, cleanup=False):
    os.path.exists(rootdir) and shutil.rmtree(rootdir)
    os.makedirs(rootdir)

    put_queue = Queue.Queue(0)
    get_queue = Queue.Queue(0)
    for path in file_paths:
        get_queue.put(path, block=False)

    installer = InstallWorker(get_queue, put_queue, rootdir, quiet=False)
    installer.setDaemon(True)
    installer.start()
    installer.join()

    if cleanup:
        for file_path in file_paths:
            os.unlink(file_path)

    result = []
    while True:
        try:
            result.append(put_queue.get(block=False))
        except Queue.Empty:
            break;

    return result

class InstallWorker(threading.Thread):
    def __init__(self, get_queue, put_queue, rootdir, quiet=True):
        super(InstallWorker, self).__init__()
        self.__putqueue = put_queue
        self.__getqueue = get_queue
        self.__rootdir = rootdir
        self.__quiet = quiet

    def __install(self, task):
        if not os.path.isdir(self.__rootdir):
            raise IOError("%s isn't directory" % self.__rootdir)

        rpmcmd = "rpm -i --nodeps --force --root=%s %s 1>/dev/null 2>&1" % \
                 (self.__rootdir, task)
        return os.system(rpmcmd)

    def run(self):
        while True:
            try:
                task = self.__getqueue.get(block=False)
                stat = self.__install(task)
                if stat == 0:
                    self.__putqueue.put(task, block=False)
                    self.__quiet or \
                    msger.info("[+] %s" % task)
                else:
                    self.__quiet or \
                    msger.error("[-] %s" % task)
            except Queue.Empty:
                break
