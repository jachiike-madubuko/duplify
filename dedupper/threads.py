import logging
import threading
import time

import queue  # must be in same directory as this file

import dedupper.utils

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s',)
BUFF_SIZE = 10000
dedupe_q = queue.Queue(BUFF_SIZE)
update_q = queue.Queue(BUFF_SIZE)
dedupe_wait_list = updates_wait_list = list()
producer= consumers = None
numThreads = 10
stopper = True
dead_threads = 0
last_thread_killed=0

class DuplifyThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        super(DuplifyThread, self).__init__()
        self.target = target
        self.name = name
        self.event = threading.Event()  #enable easy thread stopping

    def run(self):
        global dedupe_wait_list, dedupe_q
        while not self.event.is_set():
            if not dedupe_q.full():
                if dedupe_wait_list:
                    d = dedupe_wait_list.pop()
                    dedupe_q.put(d)
                else:
                    dedupe_q.put(None)
                if last_thread_killed != 0:
                    logging.debug('Time is last killed thread is {}'.format(time.time() - last_thread_killed))
                    time.sleep(5)

            if dead_threads >= numThreads-1:
                logging.debug('all consumer threads dead. producer stopped')
                stop(self)
                dedupe_q = queue.Queue(BUFF_SIZE)
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
            if last_thread_killed != 0:
                logging.debug('Time is last killed thread is {}'.format(time.time()-last_thread_killed))
            if not dedupe_q.empty():
                time.sleep(1)
                item = dedupe_q.get()
                if item is None:
                    logging.debug('Queue empty, stopping thread.')
                    stop(self)
                else:
                    dedup(item)
            else:
                logging.debug('Queue empty, stopping thread.')
                stop(self)
            if time.time()-last_thread_killed> 15  and last_thread_killed != 0:
                logging.debug('AUTO-KILL')
                stop(self)

        return

class UpdateThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        super(UpdateThread, self).__init__()
        self.target = target
        self.name = name
        self.event = threading.Event()  # enable easy thread stopping
        return

    def run(self):
        cnt = 0
        while not self.event.is_set():
            if not update_q.empty():
                time.sleep(1)
                item = update_q.get()
                if item is None:
                    time.sleep(1)

                else:
                    dedupper.utils.update_df(item)
                    cnt += 1
                    if cnt % 100 == 0:
                        print('updating dfs')

        return


def dedupeQ(newQ):
    global dedupe_wait_list
    dedupe_wait_list.extend(newQ)
    startThreads()

def updateQ(update):
    global updates_wait_list
    updates_wait_list.append(update)

def stop(x):
    global dead_threads, last_thread_killed
    dead_threads+=1
    last_thread_killed = time.time()
    x.event.set()
    logging.debug('bye: {}/{} threads killed'.format(dead_threads, numThreads))

def dedup(repNkey):
    dedupper.utils.threaded_deduping(repNkey[0], repNkey[1])

def makeThreads():
    return [DedupThread(name='dedupper' + str(i+1)) for i in range(numThreads)]

def startThreads():
    global producer, consumers, dead_threads, numThreads, last_thread_killed
    dead_threads = 0
    last_thread_killed = 0
    producer = DuplifyThread(name='producer')
    producer.start()
    u = UpdateThread(name='updater')
    u.start()
    consumers = makeThreads()
    numThreads = len(consumers)
    time.sleep(5)
    print("new number of threads {}".format(numThreads))
    [x.start() for x in consumers]

