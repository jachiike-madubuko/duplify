import threading
import time
import logging
import dedupper.utils
import random
import queue  #must be in same directory as this file

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s',)

BUF_SIZE = 10000
q = queue.Queue(BUF_SIZE)
command = list()
producer = None
consumers = None
numThreads = 12
stopper = True

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
                item = q.get()
                # logging.debug('dedupping REP ' + item[0].firstName + ' : ' + str(q.qsize()) + ' commands in queue')
                dedup(item)
            else:
                stop_threads()
        return

def updateQ(newQ):
    global command
    command.extend(newQ)
    startThreads()

def stop(x):
    x.event.set()

def stop_threads():  #all threads run on a while event is not set
    global producer, consumers, stopper
    if stopper:
        print('producer stopped')
        stop(producer)
        map(stop, consumers)
        dedupper.utils.finish(numThreads)
        stopper = False

def dedup(repNkey):
   # logging.debug('hi')
    time.sleep(random.random() * 4)
    dedupper.utils.findRepDups(repNkey[0], repNkey[1], numThreads)

def makeThreads():
    return [DedupThread(name='dedupper' + str(i)) for i in range(numThreads)]

def startThreads():
    global producer, consumers
    stopper = True
    producer = DuplifyThread(name='producer')
    consumers = makeThreads()

    producer.start()
    for i in consumers:
        i.start()
   # updateQ([('jim brown', 'firstName-territory-mailingStateProvince'),('tim harding',
# 'firstName-territory-mailingStateProvince'),('paul green', 'firstName-territory-mailingStateProvince')])
   # updateQ([('jim brown', 'Phone-lastName'),('tim harding', 'Phone-lastName'),('paul green', 'Phone-lastName')])
