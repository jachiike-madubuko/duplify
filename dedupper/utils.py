#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 19 17:53:34 2018

@author: jachi
"""
import dedupper.threads
import os
from dedupper.models import progress, repContact, sfcontact, dedupTime, duplifyTime, uploadTime
import string
from time import clock
from datetime import timedelta
from random import *
from range_key_dict import RangeKeyDict
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process #could be used to generate suggestions for unknown records
import numpy as np
from tablib import Dataset
import logging
from celery import shared_task
from celery_progress.backend import ProgressRecorder
import time


from copy import deepcopy
#find more on fuzzywuzzy at https://github.com/seatgeek/fuzzywuzzy

rkd = RangeKeyDict({
    (90, 101): 'Duplicate',
    (50, 90): 'Undecided',
    (0, 50): 'New Record'
})
waiting= True
sf_list = list(sfcontact.objects.all())
sf_map = None
start= end=cnt = 0

#TODO implement batch upload, append contacts to a list the batch save them.

def convertCSV(file, resource, type='rep', batchSize=2000):
    dataset = Dataset()
    headers = ''
    cnt, cnt2 = 0, 0
    print('converting CSV', str(file))
    start = clock()
    fileString = ''
    #look into going line by line
    for chunk in file.open():
        fileString += chunk.decode("utf-8")
        if cnt == 0:
            headers=fileString
        cnt+=1
        if cnt == batchSize:
            print('importing data' + '.'*((cnt2%3)+1))
            cnt2+=1
            cnt = 1
            dataset.csv = fileString
            resource.import_data(dataset, dry_run=False)
            fileString = headers
    dataset.csv = fileString
    resource.import_data(dataset, dry_run=False)
    end = clock()
    time = end - start
    if type == 'SF':
        uploadTime.objects.create(num_records = len(sfcontact.objects.all()), batch_size= batchSize, seconds=round(time, 2))
    else:
        uploadTime.objects.create(num_records = len(repContact.objects.all()), batch_size = batchSize, seconds=round(time, 2))
    return dataset.headers

def findRepDups(rep, keys, numthreads):
    global cnt
    start=clock()
    rep_key = rep.key(keys)
    sf_keys = [i.key(keys) for i in sf_list]
    sf_map = dict(zip(sf_keys, sf_list))

    key_matches = match_keys(rep_key, sf_keys)
    match_map = list(zip(key_matches, sf_keys))
    match_map = sorted(match_map, reverse=True)
    top1, top2, top3 = [(match_map[i][0], sf_map[match_map[i][1]]) for i in range(3)]

    if top1[0] <= top3[0] + 10 and top1[1].id != top3[1].id:
        rep.average = np.mean([top1[0], top2[0], top3[0]])
        rep.closest1 = top1[1]
        rep.closest2 = top2[1]
        rep.closest3 = top3[1]
        rep.closest1_contactID = top1[1].ContactID
        rep.closest2_contactID = top2[1].ContactID
        rep.closest3_contactID = top3[1].ContactID

    elif top1[0] <= top2[0] + 10 and top1[1].id != top2[1].id:
        rep.average = np.mean([top1[0], top2[0]])
        rep.closest1 = top1[1]
        rep.closest2 = top2[1]
        rep.closest1_contactID = top1[1].ContactID
        rep.closest2_contactID = top2[1].ContactID

    else:
        rep.average = top1[0]
        rep.closest1 = top1[1]
        rep.closest1_contactID = top1[1].ContactID
    # seperate by activity
    rep.type = sort(rep.average)
    rep.match_ID = top1[1].ContactID
    rep.save()
    time = round(clock()-start, 2)
    #update the progress object using
    #list(progress.objects.all())[-1].complete()
    dedupTime.objects.create(num_SF = len(sf_list), seconds=time, num_threads=numthreads)
    cnt+=1
    if(cnt%500==0):
        logging.debug('Completed in {} seconds'.format(time))

def finish(numThreads):
    global end, waiting
    end = clock()
    time = end - start
    duplifyTime.objects.create(num_threads=numThreads, num_SF=len(sf_list), num_rep = len(repContact.objects.all()), seconds = round(time,2))
    # print('\a')
    os.system('say "The repp list has been duplified!"')
    waiting=False


@shared_task(bind=True)
def key_generator(self,partslist):
    global start, waiting
    for key_parts in partslist:
        if 'phone' in key_parts:
            index = partslist.index(key_parts)
            del partslist[index]
            for i in ['homePhone', 'mobilePhone', 'Phone', 'otherPhone']:
                new_key_parts = [i if x == 'phone' else x for x in key_parts]
                partslist.insert(index, new_key_parts)
        if 'email' in key_parts:
            index = partslist.index(key_parts)
            del partslist[index]
            for i in ['otherEmail', 'personalEmail', 'workEmail']:
                new_key_parts = [i if x == 'email' else x for x in key_parts]
                partslist.insert(index, new_key_parts)
    progress_recorder = ProgressRecorder(self)
    start = clock()
    i=0
    for key_parts in partslist:
        print('starting key: {}'.format(key_parts))
        waiting = True
        rep_list = list(repContact.objects.filter(type__in=['Undecided', 'New Record']))
        #create progress object with reps total and title of key part
        progress_recorder.set_progress(i + 1, len(partslist))
        dedupper.threads.updateQ([[rep, key_parts] for rep in rep_list])
        while waiting:
            pass

def makeKeys(headers):
    keys = []
    total = repContact.objects.all().count()
    phoneUniqueness = 0
    emailUniqueness = 0
    # headers.replace('\r\n', '')
    # headers.replace('\n', '')
    # headers=headers.split(',')
    phoneTypes = ['Phone', 'homePhone', 'mobilePhone', 'otherPhone']
    emailTypes = ['workEmail', 'personalEmail', 'otherEmail']
    excluded = ['id', 'average', 'type', 'match_ID', 'closest1_id', 'closest2_id', 'closest3_id', 'dupFlag']

    for i in headers:
        if i not in excluded:
            if i in phoneTypes:
                phoneUniqueness += repContact.objects.order_by().values_list(i).distinct().count() / total
            elif i in emailTypes:
                emailUniqueness += repContact.objects.order_by().values_list(i).distinct().count() / total

            else:
                uniqueness = repContact.objects.order_by().values_list(i).distinct().count() / total
                keys.append((i, int(uniqueness * 100)))
    keys.extend([('phone', int((phoneUniqueness / 4) * 100)), ('email', int((emailUniqueness / 3) * 100))])
    keys.sort()
    return keys

def match_keys(key,key_list):
    for i in key_list:
        yield match_percentage(key,i)

def match_percentage(key1,key2):
    return fuzz.ratio(key1, key2)

def mutate(keys):
    mutant = keys.copy()
    num_mutating = randint(int(len(keys)/5),int(len(keys)*0.8))

    for i in range(num_mutating):
        j = randint(0,len(keys)-1)
        for i in range(randint(3,len(mutant[j])+3)):
            mutant[j]=mutant[j].replace(mutant[j][int(sample(range(len(mutant[j])-1), 1)[0])], choice(string.printable))
    return mutant

def setSortingAlgorithm(min_dup,min_uns):
    #TODO finish this function and connect it to a slider
    global rkd
    rkd = RangeKeyDict({
    (min_dup, 101): 'Duplicate',
    (min_uns, min_dup): 'Unsure',
    (0, min_uns): 'New Record'
})

def sort(avg):
    return rkd[avg]


@shared_task(bind=True)
def my_task(self,seconds):
    progress_recorder = ProgressRecorder(self)
    for i in range(seconds):
        time.sleep(1)
        progress_recorder.set_progress(i+1, seconds)
    return 'done'

