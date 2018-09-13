#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 19 17:53:34 2018

@author: jachi
"""
import logging
import os
import string
from gc import collect
from operator import itemgetter
from random import *
from time import perf_counter

import numpy as np
import pandas as pd
from django.conf import settings
from django.db.models import Avg
from fuzzyset import FuzzySet
from fuzzywuzzy import fuzz
from range_key_dict import RangeKeyDict
from simple_salesforce import Salesforce
from tablib import Dataset

import dedupper.threads
from dedupper.models import repContact, sfcontact, dedupTime, duplifyTime, uploadTime
from dedupper.resources import RepContactResource, SFContactResource

#find more on fuzzywuzzy at https://github.com/seatgeek/fuzzywuzzy


standard_sorting_range = RangeKeyDict({
    (97, 101): 'Duplicate',
    (95, 97): 'Manual Check',
    (0, 95): 'Undecided'
})
last_key_sorting_range = RangeKeyDict({
    (97, 101): 'Duplicate',
    (95, 97): 'Manual Check',
    (0, 95): 'New Record'
})
manual_sorting_range = RangeKeyDict({
    (95, 101): 'Manual Check',
    (0, 95): 'Undecided',
})
last_manual_sorting_range = RangeKeyDict({
    (95, 101): 'Manual Check',
    (0, 95): 'New Record'
})

waiting= True
keylist = list()
currKey=sort_alg=key_stats=None
start=end=cnt=doneKeys=totalKeys=0
done= False


#TODO finish phone/eemail multi sf field mapping

#TODO add docstrings go to realpython.com/documenting-python-code/
#TODO update documentation go to dbader.org/blog/write-a-great-readme-for-your-github-project
#TODO django test cases realpython <--

#simple csv to dataframe
def convert_csv(file):
    print('converting CSV: ', str(file))
    pd_csv = pd.read_csv(file, encoding = "cp1252", delimiter=',', dtype=str)  #western european
    return list(pd_csv), pd_csv

def find_rep_dups(rep, keys, numthreads):
    global cnt                          #track the number of attempted dedups
    multi_key = False                   #for tracking the one to many key generation of keys containing emails and phones
    dup_start=perf_counter()            #track the dup time
    rep_key = rep.key(keys[:-1])        #create rep key without man/dup flag
    if 'NULL' in rep_key:               #dont use key with missing parts
        logging.debug("bad rep key")
        return 0
    search_party =  sfcontact.objects.none()        #contains the contacts that have similar fields to the rep

    #refactor using Q() object
    for key in keys[:-1]:
        if 'Phone' in key:              #for phones, check the variation of phones in the sales force contact
            for type_of_phone in ['mobilePhone', 'homePhone', 'otherPhone', 'Phone']:
                # create filter for each phone variation
                kwargs = {f'{type_of_phone}__icontains': f'{rep.key([key])}'}
                # queryset of Sfcontacts that have a matching field with the rep
                search_party = search_party.union(sfcontact.objects.filter(**kwargs))
        if 'Email' in key:
            for type_of_email in ['workEmail', 'personalEmail', 'otherEmail']:
                kwargs = {f'{type_of_email}__icontains': f'{rep.key([key])}'}
                search_party = search_party.union(sfcontact.objects.filter(**kwargs))

        kwargs = { f'{key}__icontains' : f'{rep.key([key])}' }
        # queryset of Sfcontacts that have a matching field with the rep
        search_party = search_party.union(sfcontact.objects.filter(**kwargs))

    #create list of keys mapped to the contact
    sf_map = {}
    for n, i in enumerate(keys):
        if 'Phone' in i:            #create a phone variations of each key
            multi_key = True
            for j in ['mobilePhone', 'homePhone', 'otherPhone', 'Phone']:
                vary_key = keys.copy()
                vary_key[n] = j
                addon = {i.key(vary_key[:-1]) : i for i in search_party if "NULL" not in i.key(vary_key[:-1])}
                sf_map = {**sf_map, **addon} #update sf_map with variation keys
        elif 'Email' in i:          #create an email variations of each key
            multi_key = True
            for j in ['workEmail', 'personalEmail', 'otherEmail']:
                vary_key = keys.copy()
                vary_key[n] = j
                addon = {i.key(vary_key[:-1]): i for i in search_party if "NULL" not in i.key(vary_key[:-1])}
                sf_map = {**sf_map, **addon}        #update sf_map with variation keys
    if not multi_key:
        sf_map = {i.key(keys[:-1]): i for i in search_party if "NULL" not in i.key(keys[:-1])}  # only returns

    #list of keys for fuzzy mapping
    sf_keys = sf_map.keys()

    #get closest
    closest = fuzzyset_alg(rep_key, sf_keys)
    if len(closest) == 0:
         logging.debug("no close matches")
         if currKey == keylist[-1]:
            string_key = '-'.join(currKey)
            rep.keySortedBy = string_key
            rep.type = sort(1)
            rep.save()
            return
         else:
            return
    for i in closest:
        #replace key with sf contact record
        i[0] = sf_map[i[0]]
    if len(closest) == 3  and closest[0][1] <= closest[-1][1] + 10 :        #see if 3rd closest is within 10% variation
        rep.average = np.mean([closest[0][1], closest[1][1], closest[2][1]]) #compute average
        #store contacts
        rep.closest1 = closest[0][0]
        rep.closest2 = closest[1][0]
        rep.closest3 = closest[2][0]
        rep.closest1_contactID = closest[0][0].ContactID
        rep.closest2_contactID = closest[1][0].ContactID
        rep.closest3_contactID = closest[2][0].ContactID
    elif  len(closest) == 2 and closest[0][1] <= closest[-1][1] + 5: #see if 2nd  closest is within 5% variation
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

    if rep.type=='Duplicate' and rep.CRD != '' and  closest[0][0].CRD != '' and  int(rep.CRD.replace(".0","")) != int(closest[0][0].CRD.replace(".0","")) :
        rep.type = 'Manual Check'
    string_key = '-'.join(currKey)
    rep.keySortedBy = string_key
    rep.save()
    # logging.debug(f'{rep.firstName} sorted as {rep.type} with {rep.keySortedBy} key ')
    time = round(perf_counter()-dup_start, 2)

    #store time data
    dups = len(repContact.objects.filter(type='Duplicate'))
    news = len(repContact.objects.filter(type='New Record'))
    undies = len(repContact.objects.filter(type='Undecided'))
    avg = dedupTime.objects.aggregate(Avg('seconds'))['seconds__avg']
    if avg == None:
        avg = 0
    else:
        avg = round(avg, 2)
    dedupTime.objects.create(
                             seconds=time,
                             num_threads=numthreads,
                             avg=avg,
                             num_dup=dups,
                             num_new=news,
                             num_undie=undies,
                             current_key=currKey)
    cnt += 1

    #garbage collection
    del time, avg, dups, news, undies, string_key, sf_map, sf_keys, search_party, dup_start, rep_key

#reset flags and storage time
def finish(numThreads):
    global end, waiting
    c = collect()                   #garbage collection
    logging.debug(f'# of garbage collected = {c}')
    #is this the last key
    if currKey == keylist[-1]:
        #sort the remaining keys
        for i in list(repContact.objects.filter(type='Undecided')):
            if i.average != None:
                i.type = last_key_sorting_range[i.average]
            else:
                i.type = 'New Record'
            i.save()
        end = perf_counter()
        time = end - start
        duplifyTime.objects.create(num_threads=numThreads,
                                   seconds=round(time, 2)
                                   )
        os.system('say "The repp list has been duplified!"')
    waiting=False

#fuzzy match the key against the key list and returns the 3 closest from the key list
def fuzzyset_alg(key, key_list):
    finder = FuzzySet()
    finder.add(key)
    candidates = list()
    for i in key_list:
        try:
            added = [i]
            #if the match score is below 50% key error raises
            matched = finder[i]
            added.extend(*matched)
            del added[-1]       #remove rep's key from list
            added[1] *= 100      #convert to percentage
            '''
            [0] the sf key
            [1] match percentage
            '''
            candidates.append(added)
        except:
            pass
    #sort by score
    candidates.sort(key=lambda x: x[1], reverse=True)

    #take top take 10
    top_candi = candidates[:10]
    #fuzzy match and sort again
    finalist = [[i[0], fuzz.ratio(key, i[0])] for i in top_candi]
    finalist.sort(key=lambda x: x[1], reverse=True)
    del finder, candidates, top_candi
    if len(finalist) > 0:
        return finalist[:3]
    else:
        return []

#the start of duplify algorithm
def key_generator(partslist):
    global start, waiting, doneKeys, totalKeys, cnt, currKey, sort_alg, keylist
    #start timer
    start = perf_counter()
    totalKeys = len(partslist)
    #store keylist globally
    keylist = partslist
    for key_parts in partslist:
        #determine whether strong matches sort as dups or manuals
        sort_alg = key_parts[-1]
        currKey = key_parts
        cnt=0           #restarts global count
        print('starting key: {}'.format(key_parts))

        #set flags
        waiting = True
        multi_key = False

        #convert key string to list
        string_key = '-'.join(currKey)

        #get all unsorted reps
        rep_list = repContact.objects.filter(type='Undecided').exclude(keySortedBy=string_key)

        print('adding {} items to the Q'.format(len(rep_list)))
        #add reps to the thread Q
        dedupper.threads.updateQ([[rep, key_parts] for rep in rep_list])
        while waiting:
            pass
        doneKeys += 1

#uploades contacts to the db
def load_csv2db(csv, header_map, resource, file_type='rep'):
    global done
    start = perf_counter()
    dataset = Dataset()
    pd_csv = csv
    csv_header = list(pd_csv)

    try:
        if file_type=='rep':
            #concatentate the records data into a misc fields for later restoration
            pd_csv['misc'] = misc_col(csv, csv_header)
        #map replist headers to db headers
        pd_csv.rename(columns=header_map, inplace=True)
        #add id col for django import export
        pd_csv['id'] = np.nan

        #import contact records
        dataset.csv = pd_csv.to_csv()
        resource.import_data(dataset, dry_run=False)
    except:
        print("lost the pandas csv")
    end = perf_counter()    #stop timer
    time = end - start
    if file_type == 'rep':
        done = True
        uploadTime.objects.create(num_records = len(repContact.objects.all()), seconds=round(time, 2))
    else:
        uploadTime.objects.create(num_records = len(sfcontact.objects.all()),seconds=round(time, 2))
    return csv_header

# concatenates cols of the df
def misc_col(df, cols):
    from functools import reduce
    return reduce(lambda x, y: x.astype(str).str.cat(y.astype(str), sep='-!-'), [df[col] for col in cols])

#generates stats for each fields based on uniqueness of values and amount of blanks
def make_keys():
    global key_stats
    keys = []
    excluded = ['id', 'average', 'type', 'match_ID', 'closest1', 'closest2', 'closest3',
                'closest1_contactID', 'closest2_contactID', 'closest3_contactID', 'dupFlag', 'keySortedBy', 'misc']

    reps = pd.read_json(RepContactResource().export().json)
    SFs = pd.read_json(SFContactResource().export().json)
    [df.replace('', np.nan, regex=True) for df in [reps, SFs]]

    sf_count = SFs.count() / float(len(SFs)) * 100
    rep_count = reps.count() / float(len(reps)) * 100


    for i in set(reps.columns).intersection(set(SFs.columns)):
        if i not in excluded:
            if reps[i].count() != 0:
                rp_utility = int(rep_count[i])
                sf_utility = int(sf_count[i])
                rp_uniqueness = int((len(reps[i].unique()) / float(reps[i].count())) *100)
                sf_uniqueness = int((len(SFs[i].unique()) / float(SFs[i].count()))*  100)

                score =   np.average([
                        int((len(reps[i].unique()) / float(reps[i].count())) *100),
                        int(rep_count[i]),
                    int((len(SFs[i].unique()) / float(SFs[i].count()))*  100),
                    int(sf_count[i]),])

                stat = (i, rp_uniqueness, rp_utility, sf_uniqueness, sf_utility, score)
            else: stat = (i,0,0,0,0,0)
            keys.append(stat)
    keys.sort(key=itemgetter(5), reverse=True)
    key_stats=keys


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

#change the sort algorithms and resort all records
def set_sorting_algorithm(min_dup, min_uns):
    global standard_sorting_range, manual_sorting_range
    cnt=0
    standard_sorting_range = RangeKeyDict({
    (min_dup, 101): 'Manual Check',
    (0, min_dup): 'Undecided',
})

    manual_sorting_range = RangeKeyDict({
    (min_dup, 101): 'Manual Check',
    (min_uns, min_dup): 'Undecided',
    (0, min_uns): 'New Record'
})
    for rep in list(repContact.objects.all()):
        cnt+=1
        if rep.keySortedBy != '':
            keys = rep.keySortedBy.split('-')
            if keys == keylist[-1]:
                rep.type = last_key_sorting_range[rep.average]
            elif keys[-1] == 'true':
                rep.type = manual_sorting_range[rep.average]
            else:
                rep.type = standard_sorting_range[rep.average]
            rep.save()
        else:
            rep.type = standard_sorting_range[rep.average]
            rep.save()
            print('{}-{}'.format(rep.type, rep.average))

        if cnt%500 ==0:
            print('re-sort #{}'.format(cnt))

#determines which sorting algorithm will be used for the key
def sort(avg):
    if sort_alg == 'true' and currKey == keylist[-1]:
        return last_manual_sorting_range[avg]
    elif sort_alg == 'true':
        return manual_sorting_range[avg]
    elif currKey == keylist[-1]:
        return last_key_sorting_range[avg]
    else:
        return standard_sorting_range[avg]

#returns data for the progress screeen
def get_progress():
    return doneKeys, totalKeys, currKey, cnt

def get_channel(data):
    pd.DataFrame({'status':[0]}).to_json(settings.JOB_STATUS)

    global done
    channel = data['channel']
    rep_header_map = data['map']

    sf = Salesforce(password='7924Trill!', username='jmadubuko@wealthvest.com',security_token='Hkx5iAL3Al1p7ZlToomn8samW')
    query = "select Id, CRD__c, FirstName, LastName, Suffix, MailingStreet, MailingCity, MailingState, MailingPostalCode, Phone, MobilePhone, HomePhone, otherPhone, Email, Other_Email__c, Personal_Email__c   from Contact where Territory_Type__c='Geography' and Territory__r.Name like "
    starts_with = f"'{channel}%' limit 50"
    print ('querying SF')
    territory = sf.bulk.Contact.query(query + starts_with)
    print(len(territory))
    territory = pd.DataFrame(territory).drop('attributes', axis=1).replace([None], [''], regex=True)
    sf_header_map = {
           'CRD__c': 'CRD',
           'Email': 'workEmail',
           'FirstName': 'firstName',
           'HomePhone': 'homePhone',
           'Id': 'ContactID',
           'LastName': 'lastName',
           'MailingCity': 'mailingCity',
           'MailingPostalCode': 'mailingZipPostalCode',
           'MailingState': 'mailingStateProvince',
           'MailingStreet': 'mailingStree t',
           'MobilePhone': 'mobilePhone',
           'OtherPhone': 'otherPhone',
           'Phone': 'Phone',
           'Personal_Email__c': 'personalEmail',
           'Other_Email__c': 'otherEmail',
           'Suffix': 'suffix',
                       }
    sfcontact_resource = SFContactResource()
    repcontact_resource = RepContactResource()
    print('loading sf: STARTED')
    load_csv2db(territory, sf_header_map, sfcontact_resource, file_type='SF')
    print('loading sf: DONE')

    pd_rep_csv = pd.read_pickle(settings.REP_CSV)
    print('loading rep: STARTED')
    load_csv2db(pd_rep_csv.head(50), rep_header_map, repcontact_resource)
    print('loading rep: DONE')
    print('key stats: STARTED')
    make_keys()
    print('key stats: DONE')
    print('job: DONE')
    pd.DataFrame({'status': [1]}).to_json(settings.JOB_STATUS)
def get_key_stats():
    return key_stats

def db_done():
    d= pd.read_json(settings.JOB_STATUS)
    status =list(d['status'] == 1)[0]
    print (f'status: {status}')
    return status
