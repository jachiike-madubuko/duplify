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
            for i in ['homePhone', 'mobilePhone', 'workPhone']:
                new_key_parts = [i if x == 'phone' else x for x in key_parts]
                partslist.insert(index, new_key_parts)
        if 'email' in key_parts:
            index = partslist.index(key_parts)
            del partslist[index]
            for i in ['otherEmail', 'personalEmail', 'workEmail']:
                new_key_parts = [i if x == 'email' else x for x in key_parts]
                partslist.insert(index, new_key_parts)

    sf_list = list(SFContact.objects.all())
    # for key_parts in partslist:
    rep_list = list(RepContact.objects.filter(type__in=['Undecided', 'New Record']))
    rep_keys = [i.key(partslist[0]) for i in rep_list]
    start = clock()
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

        if top1[0] <= top3[0]+25:
            person.average = np.mean([top1[0], top2[0], top3[0]])
            person.closest1 = top1[1]
            person.closest2 = top2[1]
            person.closest3 = top3[1]
        elif top1[0] <= top2[0]+25:
            person.average = np.mean([top1[0], top2[0]])
            person.closest1 = top1[1]
            person.closest2 = top2[1]
        else:
            person.average = top1[0]
            person.closest1 = top1[1]
        #seperate by activity
        person.type = sort(person.average)
        #try-catch for the save, error will raise if match_contactID is not unique
        person.save()

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
    for i in headers:
        if 'Phone' in i:
            phoneUniqueness += RepContact.objects.order_by().values_list(i).distinct().count() / total
        if 'Email' in i:
            emailUniqueness += RepContact.objects.order_by().values_list(i).distinct().count() / total
        else:
            uniqueness = RepContact.objects.order_by().values_list(i).distinct().count() / total
            keys.append((i, int(uniqueness * 100)))
    keys.extend([('phone', int((phoneUniqueness / 3) * 100)), ('email', int((emailUniqueness / 3) * 100))])
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

    fileString = ''
    for chunk in file.chunks():
        fileString += chunk.decode("utf-8") + '\n'
    print('done decoding')
    # needs id col as 1st col
    print('load data')
    dataset.csv = fileString
    print('done data load')
    result = resource.import_data(dataset, dry_run=True)  # Test the data import
    if not result.has_errors():
        print('importing data')
        resource.import_data(dataset, dry_run=False)  # Actually import now

    return dataset.headers


