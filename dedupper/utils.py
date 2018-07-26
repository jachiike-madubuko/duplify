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
import json
import pandas as pd
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
keylist = list()
sf_keys = list()
sf_list = list(sfcontact.objects.all())
sf_map=currKey=sort_alg=None
start=end=cnt=doneKeys=totalKeys=0


def convert_csv(file):
    print('converting CSV: ', str(file))
    pd_csv = pd.read_csv(file, encoding = "utf-8")
    return list(pd_csv), pd_csv

def find_rep_dups(rep, keys, numthreads):
    global cnt
    dup_start=perf_counter()
    rep_key = rep.key(keys[:-1])
    if 'NULL' in rep_key:
        return 0
    closest = fuzzyset_alg(rep_key, sf_keys)
    if len(closest) == 0:
        return
    for i in closest:
        i[0] = sf_map[i[0]] #replace key with sf contact record
    # try:
    #     closest[0], closest[1], closest[2] = [(match_map[i][0], sf_map[match_map[i][1]]) for i in range(3)]
    # except Exception as e:
    #     logging.exception(e)
    #     print("ERROR\n\t match_map:\t{}\n\t key_matches:\t{}\n\t sf_map:\t{}\n\t sf_keys:\t{}\n\t ".format(match_map,
    #                                                                                                        key_matches,
    #                                                                                                        sf_map,
    #                                                                                                        sf_keys))
    if closest[0][1] <= closest[-1][1] + 10 and len(closest) == 3:
        rep.average = np.mean([closest[0][1], closest[1][1], closest[2][1]])
        rep.closest1 = closest[0][0]
        rep.closest2 = closest[1][0]
        rep.closest3 = closest[2][0]
        rep.closest1_contactID = closest[0][0].ContactID
        rep.closest2_contactID = closest[1][0].ContactID
        rep.closest3_contactID = closest[2][0].ContactID
    elif closest[0][1] <= closest[-1][1] + 10 and len(closest) == 2:
        rep.average = np.mean([closest[0][1], closest[1][1]])
        rep.closest1 = closest[0][0]
        rep.closest2 = closest[1][0]
        rep.closest1_contactID = closest[0][0].ContactID
        rep.closest2_contactID = closest[1][0].ContactID
    else:
        rep.average = closest[0][1]
        rep.closest1 = closest[0][0]
        rep.closest1_contactID = closest[0][0].ContactID
    rep.type = sort(rep.average)

    if rep.CRD != closest[0][0].CRD:
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
    finder = FuzzySet(use_levenshtein=False)
    finder.add(key)
    candidates = list()
    for i in key_list:
        try:
            added = [i]
            matched = finder[i]
            added.extend(*matched)
            del added[-1]  #remove rep's key from list
            added[1] *= 100
            '''
            [0] the sf key
            [1] match percentage
            '''
            candidates.append(added)
        except:
            pass
    candidates.sort(key=lambda x: x[1], reverse=True)
    # print("###############################################\n candidates \n {}\n".format(candidates))
    top_candi = candidates[:10]
    finalist = [[i[0], fuzz.ratio(key, i[0])] for i in top_candi]
    finalist.sort(key=lambda x: x[1], reverse=True)
    if len(finalist) > 0:
        return finalist[:1]
    else:
        return []

def key_generator(partslist):
    global start, waiting, doneKeys, totalKeys, cnt, currKey, sort_alg, keylist, sf_keys, sf_map
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
        sf_map = {i.key(key_parts[:-1]) : i for i in sf_list if "NULL" not in i.key(key_parts[:-1]) } #only returns
        sf_print_map = {i.key(key_parts[:-1]) : str(i) for i in sf_list if "NULL" not in i.key(key_parts[:-1]) } #only returns
        # print(json.dumps(sf_print_map, indent=4))
        sf_keys = sf_map.keys()
        # sf_keys
        # that
        # have all the fields in the key
        rep_list = list(repContact.objects.filter(type='Undecided'))
        dedupper.threads.updateQ([[rep, key_parts] for rep in rep_list])
        while waiting:
            pass
        doneKeys += 1

def load_csv2db(csv, header_map, resource, file_type='rep'):
    start = perf_counter()
    dataset = Dataset()
    pd_csv = csv
    print(list(pd_csv))
    print(json.dumps(header_map, indent=4))
    try:
        pd_csv.rename(columns=header_map, inplace=True)
        pd_csv['id'] = np.nan
    except:
        print("lost the pandas csv")
    print(list(pd_csv))
    dataset.csv = pd_csv.to_csv()
    results = resource.import_data(dataset, dry_run=False)
    end = perf_counter()
    time = end - start
    if file_type == 'rep':
        uploadTime.objects.create(num_records = len(repContact.objects.all()), seconds=round(time, 2))
    else:
        uploadTime.objects.create(num_records = len(sfcontact.objects.all()),seconds=round(time, 2))

def make_keys(headers):
    keys = []
    rep_total = repContact.objects.all().count()
    sf_total = sfcontact.objects.all().count()
    phoneUniqueness = 0
    emailUniqueness = 0
    phoneTypes = ['Phone', 'homePhone', 'mobilePhone', 'otherPhone']
    emailTypes = ['workEmail', 'personalEmail', 'otherEmail']
    excluded = ['id', 'average', 'type', 'match_ID', 'closest1', 'closest2', 'closest3',
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
