#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 19 17:53:34 2018

@author: jachi
"""

import os
from dedupper.models import Simple, RepContact, SFContact
import string
from time import clock
from random import *
from range_key_dict import RangeKeyDict
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process #could be used to generate suggestions for unknown records
import numpy as np
from tablib import Dataset

from copy import deepcopy
#find more on fuzzywuzzy at https://github.com/seatgeek/fuzzywuzzy

rkd = RangeKeyDict({
    (100, 101): 'Duplicate',
    (70, 100): 'Undecided',
    (0, 70): 'New Record'
})

def key_generator(partslist):
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
        print('KEY:', end='\t')
        for i in key_parts:
            print(i,end='\t' )
        rep_list = list(RepContact.objects.filter(type__in=['Undecided', 'New Record']))
        rep_keys = [i.key(key_parts) for i in rep_list]
        rep_map = dict(zip(rep_keys, rep_list))
        print("################################")
        sf_keys = [i.key(partslist[0]) for i in sf_list]
        sf_map = dict(zip(sf_keys, sf_list))

        for rep_key in rep_keys:
            key_matches = match_keys(rep_key, sf_keys)
            match_map = list(zip(key_matches, sf_keys))
            match_map = sorted(match_map, reverse=True)
            top1, top2, top3 = [(match_map[i][0], sf_map[match_map[i][1]]) for i in range(3)]
            person = rep_map[rep_key]

            if top1[0] <= top3[0]+25 and top1[1].id != top3[1].id:
                person.average = np.mean([top1[0], top2[0], top3[0]])
                person.closest1 = top1[1]
                person.closest2 = top2[1]
                person.closest3 = top3[1]
            elif top1[0] <= top2[0]+25 and top1[1].id != top2[1].id:
                person.average = np.mean([top1[0], top2[0]])
                person.closest1 = top1[1]
                person.closest2 = top2[1]
            else:
                person.average = top1[0]
                person.closest1 = top1[1]
            person.match_ID = top1[1].ContactID
            #seperate by activity
            person.type = sort(person.average)
            #try-catch for the save, error will raise if match_contactID is not unique
            person.save()
            print("{} saved at {}".format(person.firstName, str(clock()-start)))

    end = clock()
    time = str(end - start)
    print('...dedupping and sorting complete \t time = ' + time)
    print('\a')
    os.system('say "The repp list has been duplified!"')

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


