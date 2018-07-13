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
from random import *
from range_key_dict import RangeKeyDict
from fuzzywuzzy import fuzz
from fuzzywuzzy import process #could be used to generate suggestions for unknown records
import numpy as np
from tablib import Dataset
import logging
import time
from django.db.models import Avg

from operator import itemgetter
#find more on fuzzywuzzy at https://github.com/seatgeek/fuzzywuzzy


dup_rkd = RangeKeyDict({
    (98, 101): 'Duplicate',
    (70, 98): 'Undecided',
    (0, 70): 'New Record'
})

man_rkd = RangeKeyDict({
    (98, 101): 'Manual Check',
    (70, 98): 'Undecided',
    (0, 70): 'New Record'
})


waiting= True
sf_list = list(sfcontact.objects.all())
sf_map=currKey=sort_alg = None
start=end=cnt=doneKeys=totalKeys = 0
keylist = list()


def convert_csv(file, resource, type='rep', batchSize=3000):
    dataset = Dataset()
    headers = ''
    cnt, cnt2 = 0, 0
    print('converting CSV ', str(file))
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

def find_rep_dups(rep, keys, numthreads):
    global cnt
    dup_start=clock()
    rep_key = rep.key(keys)
    sf_keys = [i.key(keys) for i in sf_list]
    sf_map = dict(zip(sf_keys, sf_list))
    key_matches = match_keys(rep_key, sf_keys)
    match_map = list(zip(key_matches, sf_keys))
    match_map = sorted(match_map, reverse=True)
    top1, top2, top3 = [(match_map[i][0], sf_map[match_map[i][1]]) for i in range(3)]
    # try:
    #     top1, top2, top3 = [(match_map[i][0], sf_map[match_map[i][1]]) for i in range(3)]
    # except Exception as e:
    #     logging.exception(e)
    #     print("ERROR\n\t match_map:\t{}\n\t key_matches:\t{}\n\t sf_map:\t{}\n\t sf_keys:\t{}\n\t ".format(match_map,
    #                                                                                                        key_matches,
    #                                                                                                        sf_map,
    #                                                                                                        sf_keys))

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
        rep.type = sort(rep.average)

    if rep.CRD != top1[1].CRD:
        rep.dupFlag = True
    string_key = '-'.join(currKey)
    rep.keySortedBy = string_key
    rep.save()
    time = round(clock()-dup_start, 2)
    avg = dedupTime.objects.aggregate(Avg('seconds'))['seconds__avg']
    if avg == None:
        avg = 0
    else:
        avg = round(avg, 2)
    dups = len(repContact.objects.filter(type='Duplicate'))
    news = len(repContact.objects.filter(type='New Record'))
    undies = len(repContact.objects.filter(type='Undecided'))
    dedupTime.objects.create(num_SF = len(sf_list),
                             seconds=time,
                             num_threads=numthreads,
                             avg=avg,
                             num_dup=dups,
                             num_new=news,
                             num_undie=undies,
                             current_key=currKey)
    cnt += 1

def finish(numThreads):
    global end, waiting
    if currKey == keylist[-1]:
        end = clock()
        time = end - start
        duplifyTime.objects.create(num_threads=numThreads,
                                   num_SF=len(sf_list),
                                   num_rep=len(repContact.objects.all()),
                                   seconds=round(time, 2)
                                   )
        os.system('say "The repp list has been duplified!"')
    waiting=False

def key_generator(partslist):
    global start, waiting, doneKeys, totalKeys, cnt, currKey, sort_alg, keylist
    start = clock()
    totalKeys = len(partslist)
    keylist = partslist
    for key_parts in partslist:
        sort_alg = key_parts.pop()
        currKey = key_parts
        cnt=0
        print('starting key: {}'.format(key_parts))
        waiting = True
        rep_list = list(repContact.objects.filter(type='Undecided'))
        dedupper.threads.updateQ([[rep, key_parts] for rep in rep_list])
        while waiting:
            pass
        doneKeys += 1

def make_keys(headers):
    keys = []
    total = repContact.objects.all().count()
    phoneUniqueness = 0
    emailUniqueness = 0
    phoneTypes = ['Phone', 'homePhone', 'mobilePhone', 'otherPhone']
    emailTypes = ['workEmail', 'personalEmail', 'otherEmail']
    excluded = ['id', 'average', 'type', 'match_ID', 'closest1_id', 'closest2_id', 'closest3_id',
                'closest1_contactID', 'closest2_contactID', 'closest3_contactID', 'dupFlag', 'keySortedBy' ]

    for i in headers:
        if i not in excluded:
            uniqueness = repContact.objects.order_by().values_list(i).distinct().count() / total
            keys.append((i, int(uniqueness * 100)))
    keys.sort(key=itemgetter(1), reverse=True)
    return keys

def match_keys(key,key_list):
    for i in key_list:
        yield match_percentage(key, i)

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

def set_sorting_algorithm(min_dup, min_uns):
    global rkd
    rkd = RangeKeyDict({
    (min_dup, 101): 'Duplicate',
    (min_uns, min_dup): 'Unsure',
    (0, min_uns): 'New Record'
})
    #TODO function to loop through the records and resort them based on new RKD

def sort(avg):
    if(sort_alg == 'true'):
        return man_rkd[avg]
    else:
        return dup_rkd[avg]

def get_progress():
    return doneKeys, totalKeys, currKey, cnt



