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
from time import perf_counter
from random import *
from range_key_dict import RangeKeyDict
from fuzzywuzzy import fuzz
from fuzzywuzzy import process #could be used to generate suggestions for unknown records
import numpy as np
from tablib import Dataset
import logging
import time
from django.db.models import Avg
from fuzzyset import FuzzySet
from operator import itemgetter
import ast
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
sf_keys = list()
start=end=cnt=doneKeys=totalKeys = 0
keylist = list()


def convert_csv(file, resource, type='rep', batchSize=3000):
    dataset = Dataset()
    headers = ''
    cnt, cnt2 = 0, 0
    print('converting CSV ', str(file))
    start = perf_counter()
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
    end = perf_counter()
    time = end - start
    if type == 'SF':
        uploadTime.objects.create(num_records = len(sfcontact.objects.all()), batch_size= batchSize, seconds=round(time, 2))
    else:
        uploadTime.objects.create(num_records = len(repContact.objects.all()), batch_size = batchSize, seconds=round(time, 2))
    return dataset.headers

def find_rep_dups(rep, keys, numthreads):
    global cnt
    dup_start=perf_counter()
    rep_key = rep.key(keys[:-1])
    if 'NULL' in rep_key:
        return 0

    sf_map = dict(zip(sf_keys, sf_list))
    top1, top2, top3 = fuzzyset_alg(rep_key, sf_keys)
    for i in [top1, top2, top3]:
        i[0] = sf_map[i[0]]
    # try:
    #     top1, top2, top3 = [(match_map[i][0], sf_map[match_map[i][1]]) for i in range(3)]
    # except Exception as e:
    #     logging.exception(e)
    #     print("ERROR\n\t match_map:\t{}\n\t key_matches:\t{}\n\t sf_map:\t{}\n\t sf_keys:\t{}\n\t ".format(match_map,
    #                                                                                                        key_matches,
    #                                                                                                        sf_map,
    #                                                                                                        sf_keys))
    if top1[1] <= top3[1] + 5 and top1[0].id != top3[0].id:
        rep.average = np.mean([top1[1], top2[1], top3[1]])
        rep.closest1 = top1[0]
        rep.closest2 = top2[0]
        rep.closest3 = top3[0]
        rep.closest1_contactID = top1[0].ContactID
        rep.closest2_contactID = top2[0].ContactID
        rep.closest3_contactID = top3[0].ContactID
    elif top1[1] <= top2[1] + 5 and top1[0].id != top2[0].id:
        rep.average = np.mean([top1[1], top2[1]])
        rep.closest1 = top1[0]
        rep.closest2 = top2[0]
        rep.closest1_contactID = top1[0].ContactID
        rep.closest2_contactID = top2[0].ContactID
    else:
        rep.average = top1[1]
        rep.closest1 = top1[0]
        rep.closest1_contactID = top1[0].ContactID
    rep.type = sort(rep.average)

    if rep.CRD != top1[0].CRD:
        rep.dupFlag = True
    string_key = '-'.join(currKey)
    rep.keySortedBy = string_key
    rep.save()
    time = round(perf_counter()-dup_start, 2)

    dups = len(repContact.objects.filter(type='Duplicate'))
    news = len(repContact.objects.filter(type='New Record'))
    undies = len(repContact.objects.filter(type='Undecided'))
    avg = dedupTime.objects.aggregate(Avg('seconds'))['seconds__avg']
    if avg == None:
        avg = 0
    else:
        avg = round(avg, 2)
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
        end = perf_counter()
        time = end - start
        duplifyTime.objects.create(num_threads=numThreads,
                                   num_SF=len(sf_list),
                                   num_rep=len(repContact.objects.all()),
                                   seconds=round(time, 2)
                                   )
        os.system('say "The repp list has been duplified!"')
    waiting=False

def fuzzyset_alg(key, key_list):
    finder = FuzzySet()
    finder.add(key)
    candidates = list()
    for i in key_list:
        try:
            added = [i]
            matched = finder[i]
            added.extend(*matched)
            del added[-1]  #remove rep's key from list
            added[1] *= 100
            candidates.append(added)
        except:
            pass
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0:3]

def key_generator(partslist):
    global start, waiting, doneKeys, totalKeys, cnt, currKey, sort_alg, keylist, sf_keys
    start = perf_counter()
    totalKeys = len(partslist)
    keylist = partslist
    for key_parts in partslist:
        sort_alg = key_parts[-1]
        currKey = key_parts
        cnt=0
        print('starting key: {}'.format(key_parts))
        waiting = True
        multi_key = False
        #TODO test this one to many code
        '''
        for n,i in enumerate(key_parts):
            if 'Phone' in i:
                multi_key = True
                sf_keys = []
                for j in ['mobilePhone', 'homePhone', 'otherPhone', 'Phone']:
                    vary_key = key_parts.copy()
                    vary_key[n] = j
                    addon = [i.key(vary_key[:-1]) for i in sf_list if "NULL" not in i.key(vary_key[:-1]) ]
                    sf_keys.extend(addon)
            elif 'Email' in i:
                multi_key = True
                sf_keys = []
                for j in ['workEmail', 'personalEmail', 'otherEmail']:
                    vary_key = key_parts.copy()
                    vary_key[n] = j
                    addon = [i.key(vary_key[:-1]) for i in sf_list if "NULL" not in i.key(vary_key[:-1]) ]
                    sf_keys.extend(addon)
        if not multi_key:
            sf_keys = [i.key(key_parts[:-1]) for i in sf_list if "NULL" not in i.key(key_parts[:-1]) ] #only returns    
        '''
        sf_keys = [i.key(key_parts[:-1]) for i in sf_list if "NULL" not in i.key(key_parts[:-1]) ] #only returns
        # sf_keys
        # that
        # have all the fields in the key
        rep_list = list(repContact.objects.filter(type='Undecided'))
        dedupper.threads.updateQ([[rep, key_parts] for rep in rep_list])
        while waiting:
            pass
        doneKeys += 1

def make_keys(headers):
    keys = []
    rep_total = repContact.objects.all().count()
    sf_total = sfcontact.objects.all().count()
    phoneUniqueness = 0
    emailUniqueness = 0
    phoneTypes = ['Phone', 'homePhone', 'mobilePhone', 'otherPhone']
    emailTypes = ['workEmail', 'personalEmail', 'otherEmail']
    excluded = ['id', 'average', 'type', 'match_ID', 'closest1_id', 'closest2_id', 'closest3_id',
                'closest1_contactID', 'closest2_contactID', 'closest3_contactID', 'dupFlag', 'keySortedBy' ]

    for i in headers:
        if i not in excluded:
            kwargs = {
                '{}__{}'.format(i, 'exact'):''
            }
            rp_uniqueness = repContact.objects.order_by().values_list(i).distinct().count() / rep_total
            rp_utility = (len(repContact.objects.all()) - len(repContact.objects.filter(**kwargs))) /rep_total
            sf_uniqueness = sfcontact.objects.order_by().values_list(i).distinct().count() / sf_total
            sf_utility = (len(sfcontact.objects.all()) - len(sfcontact.objects.filter(**kwargs))) /sf_total
            score = (rp_uniqueness + rp_utility + sf_uniqueness + sf_utility)/4
            keys.append((i, int(rp_uniqueness * 100), int(rp_utility * 100), int(sf_uniqueness * 100), int(sf_utility * 100), score))
    keys.sort(key=itemgetter(5), reverse=True)
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
    global dup_rkd, man_rkd
    cnt=0
    dup_rkd = RangeKeyDict({
    (min_dup, 101): 'Duplicate',
    (min_uns, min_dup): 'Undecided',
    (0, min_uns): 'New Record'
})

    man_rkd = RangeKeyDict({
    (min_dup, 101): 'Manual Check',
    (min_uns, min_dup): 'Undecided',
    (0, min_uns): 'New Record'
})
    for rep in list(repContact.objects.all()):
        cnt+=1
        if rep.keySortedBy != '':
            keys = rep.keySortedBy.split('-')
            if keys[-1] == 'true':
                rep.type = man_rkd[rep.average]
            else:
                rep.type = dup_rkd[rep.average]
            rep.save()
        else:
            rep.type = dup_rkd[rep.average]
            rep.save()
            print('{}-{}'.format(rep.type, rep.average))

        if cnt%500 ==0:
            print('re-sort #{}'.format(cnt))

def sort(avg):
    if(sort_alg == 'true'):
        return man_rkd[avg]
    else:
        return dup_rkd[avg]

def get_progress():
    return doneKeys, totalKeys, currKey, cnt

#function to force quit all threads remaining
'''
for all consumer 
    if event is not set 
        set event 
'''