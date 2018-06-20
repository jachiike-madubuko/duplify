#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 19 17:53:34 2018

@author: jachi
"""
from dedupper.threads import updateQ
import os
from dedupper.models import Simple, RepContact, SFContact, DedupTime, DuplifyTime, UploadTime
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

from copy import deepcopy
#find more on fuzzywuzzy at https://github.com/seatgeek/fuzzywuzzy

rkd = RangeKeyDict({
    (100, 101): 'Duplicate',
    (70, 100): 'Undecided',
    (0, 70): 'New Record'
})
waiting= True
sf_list = list(SFContact.objects.all())
sf_map = None
start = 0
end = 0

def key_generator(partslist):
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
    start = clock()
    sf_list = list(SFContact.objects.all())
    for key_parts in partslist:
        waiting = True
        rep_list = list(RepContact.objects.filter(type__in=['Undecided', 'New Record']))
        updateQ([[rep,key_parts] for rep in rep_list])
        while waiting:
            pass

        ###in threads
        ###when Q in empty
        ### call function drop_flag
        ##def drop_flag(): = False


def match_keys(key,key_list):
    for i in key_list:
        yield match_percentage(key,i)

def sort(avg):
    return rkd[avg]

def match_percentage(key1,key2):
    return fuzz.ratio(key1, key2)

def setSortingAlgorithm(min_dup,min_uns):
    #TODO finish this function and connect it to a slider
    global rkd
    rkd = RangeKeyDict({
    (min_dup, 101): 'Duplicate',
    (min_uns, min_dup): 'Unsure',
    (0, min_uns): 'New Record'
})

def makeKeys(headers):
    keys = []
    total = RepContact.objects.all().count()
    phoneUniqueness = 0
    emailUniqueness = 0
    print(headers)
    headers = headers.replace('\r\n', '')
    print(headers)
    headers=headers.split(',')
    print(headers)

    for i in headers:
        if 'Phone' in i:
            phoneUniqueness += RepContact.objects.order_by().values_list(i).distinct().count() / total
        if 'Email' in i:
            emailUniqueness += RepContact.objects.order_by().values_list(i).distinct().count() / total
        else:
            uniqueness = RepContact.objects.order_by().values_list(i).distinct().count() / total
            keys.append((i, int(uniqueness * 100)))
    keys.extend([('phone', int((phoneUniqueness / 4) * 100)), ('email', int((emailUniqueness / 3) * 100))])
    keys.sort()
    return keys

def mutate(keys):
    mutant = keys.copy()
    num_mutating = randint(int(len(keys)/5),int(len(keys)*0.8))

    for i in range(num_mutating):
        j = randint(0,len(keys)-1)
        for i in range(randint(3,len(mutant[j])+3)):
            mutant[j]=mutant[j].replace(mutant[j][int(sample(range(len(mutant[j])-1), 1)[0])], choice(string.printable))
    return mutant

def convertCSV(file, resource):
    dataset = Dataset()
    headers = ''
    cnt, cnt2 = 0, 0
    print('converting CSV' + str(file))
    start = clock()
    fileString = ''
    #look into going line by line
    for chunk in file.open():
        fileString += chunk.decode("utf-8")
        if cnt == 0:
            headers=fileString
        cnt+=1
        if cnt == 2000:
            print('importing data' + '.'*((cnt2%3)+1))
            cnt2+=1
            cnt = 1
            dataset.csv = fileString
            resource.import_data(dataset, dry_run=False)
            fileString = headers
    dataset.csv = fileString
    resource.import_data(dataset, dry_run=False)
    end = clock()
    time = str(end - start)
    print('...upload complete \t time = ' + time)
    return headers

def duplify(rep, keys, numthreads):
    start=clock()
    rep_key = rep.key(keys)
    # logging.debug(rep_key)
    sf_keys = [i.key(keys) for i in sf_list]
    sf_map = dict(zip(sf_keys, sf_list))
   # logging.debug(sf_map)
    
    key_matches = match_keys(rep_key, sf_keys)
    match_map = list(zip(key_matches, sf_keys))
    match_map = sorted(match_map, reverse=True)
    top1, top2, top3 = [(match_map[i][0], sf_map[match_map[i][1]]) for i in range(3)]

    if top1[0] <= top3[0] + 15 and top1[1].id != top3[1].id:
        rep.average = np.mean([top1[0], top2[0], top3[0]])
        rep.closest1 = top1[1]
        rep.closest2 = top2[1]
        rep.closest3 = top3[1]
    elif top1[0] <= top2[0] + 15 and top1[1].id != top2[1].id:
        rep.average = np.mean([top1[0], top2[0]])
        rep.closest1 = top1[1]
        rep.closest2 = top2[1]
    else:
        rep.average = top1[0]
        rep.closest1 = top1[1]
    # seperate by activity
    rep.type = sort(rep.average)

    if rep.type != "New Record":
        rep.match_ID = top1[1].ContactID
    else:
        rep.match_ID = ''
    # try-catch for the save, error will raise if match_contactID is not unique
    rep.dupFlag = True
    rep.save()
    end = clock()
    DedupTime.objects.create(num_SF = len(sf_list), seconds=timedelta(seconds=int(end-start)), num_threads=numthreads)
    #logging.debug('bye')

def finish(numThreads):
    global end, waiting
    end = clock()
    time = end - start
    DuplifyTime.objects.create(num_threads=numThreads, num_SF=len(sf_list), num_rep = len(RepContact.objects.all()),
                               seconds = timedelta(seconds=int(time)))
    #print('...dedupping and sorting complete \t time = ' + time)
    print('\a')
    os.system('say "The repp list has been duplified!"')
    waiting=False


