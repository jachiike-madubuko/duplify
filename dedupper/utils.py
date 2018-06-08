#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 19 17:53:34 2018

@author: jachi
"""
from dedupper.models import Simple
import string
from time import clock
from random import *
from range_key_dict import RangeKeyDict
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process #could be used to generate suggestions for unknown records
import numpy as np
#find more on fuzzywuzzy at https://github.com/seatgeek/fuzzywuzzy

df = None
dups = list()
new_records = list()
unsure = list()

rkd = RangeKeyDict({
    (100, 101): 'Duplicate',
    (70, 100): 'Undecided',
    (0, 70): 'New Record'
})

"""
TODO clean up comments
TODO stage functionality for saving csv (pandas to csv)
TODO
"""


def key_generator(partslist):
    #for each row in df
        #concatenate each columns in headers
        #store key in new list
    print(partslist)
    #for key_parts in partslist:
    #Simple.objects.filter(type__exact='Unsure')
    rep_list = list(Simple.objects.all())
    rep_keys = [i.key(partslist[0]) for i in rep_list]
    rep_map = dict(zip(rep_keys,rep_list))

    #sf_list = list(Contact.object.all())
    #sf_keys = [i.key(partslist[0]) for i in sf_list]
    #sf_map = dict(zip(sf_keys, sf_list))
    sf_keys = mutate(rep_keys)

    for rep_key in rep_keys:
        key_matches = match_keys(rep_key,sf_keys)
        match_map = list(zip(key_matches,sf_keys))
        match_map  = sorted(match_map, reverse=True)
        top1, top2, top3 = [match_map[0], match_map[1], match_map[2]]
        person = rep_map[rep_key]

        if top1[0] <= top3[0]+25:
            person.average = np.mean([top1[0],top2[0],top3[0]])
            person.closest1 = top1
            person.closest2 = top2
            person.closest3 = top3
        elif top1[0] <= top2[0]+25:
            person.average = np.mean([top1[0],top2[0]])
            person.closest1 = top1
            person.closest2 = top2
        else:
            person.average = top1[0]
            person.closest1 = top1

        #seperate by activity

        person.type  = sort(person.average)

        person.save()
    print('\a')


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

def classify_records(key1, key2):
    percent = match_percentage(key1,key2)
    return(rkd[percent],str(percent)+'%')

def mutate(keys):
    mutant = keys.copy()
    num_mutating = randint(int(len(keys)/5),int(len(keys)*0.8))

    for i in range(num_mutating):
        j = randint(0,len(keys)-1)
        for i in range(randint(3,len(mutant[j])+3)):
            mutant[j]=mutant[j].replace(mutant[j][int(sample(range(len(mutant[j])-1), 1)[0])], choice(string.printable))
    return mutant

def sorter(group, index,percent):
    global dups, new_records, unsure,df
    record = list(df.iloc[index])
    record.append(percent)
    if(group == 'Duplicate'):
        dups.append(record)
    elif(group == 'New Record'):
        new_records.append(record)
#    elif(group == 'Unsure'):
#        unsure.append(record)

def dedup(key):
    print('...entering dedup process')
    start = clock()
    sorted_bin = []
    #only dedup unsure list, aka start off with the keys
    #in the unsure list, pop them into new list or leave them
    #then iterate thru key set
    sf_list=mutate(key)

    for i in range(len(key)):
        classify,percent = classify_records(key[i],sf_list[i])
        sorter(classify, i, percent)
        if(classify != 'Unsure'):
            sorted_bin.append(i)
    df.drop(df.index[sorted_bin], inplace = True)
    end = clock()
    time = str(end-start)
    print('...dedupping and sorting complete \t time = '+time)

def get_lists():
    return(dups, new_records, list(df.values))