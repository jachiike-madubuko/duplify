import threading
import time
import logging
import dedupper.utils
import random
import queue  #must be in same directory as this file

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s',)

BUFF_SIZE = 10000
q = queue.Queue(BUFF_SIZE)
command = list()
producer= consumers = None
numThreads = 12
stopper = True
dead_threads = 0

class DuplifyThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        super(DuplifyThread, self).__init__()
        self.target = target
        self.name = name
        self.event = threading.Event()  #enable easy thread stopping

    def run(self):
        global command
        while not self.event.is_set():
            if not q.full():
                if command:
                    d = command.pop()
                    q.put(d)
            if dead_threads == numThreads:
                print('all consumer threads dead. producer stopped')
                stop(self)
                dedupper.utils.finish(numThreads)

        return

class DedupThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        super(DedupThread, self).__init__()
        self.target = target
        self.name = name
        self.event = threading.Event()   #enable easy thread stopping
        return

    def run(self):
        while not self.event.is_set():
            ''' switch based on name of consumer thread
            face should look at a static variable
            'action' updated after q.get '''
            if not q.empty():
                dedup(q.get())
            else:
                logging.debug('Queue empty, stopping thread')
                stop(self)
        return

def updateQ(newQ):
    global command
    command.extend(newQ)
    startThreads()

def stop(x):
    global dead_threads
    x.event.set()
    dead_threads+=1
    logging.debug('bye: {}/{} threads killed'.format(dead_threads,numThreads))

def dedup(repNkey):
    dedupper.utils.findRepDups(repNkey[0], repNkey[1], numThreads)

def makeThreads():
    return [DedupThread(name='dedupper' + str(i+1)) for i in range(numThreads)]

def startThreads():
    global producer, consumers, dead_threads
    dead_threads = 0
    producer = DuplifyThread(name='producer')
    consumers = makeThreads()
    producer.start()
    [x.start() for x in consumers]

