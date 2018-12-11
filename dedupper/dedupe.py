import logging
import os
import string
from functools import reduce
from gc import collect
from io import StringIO
from operator import itemgetter
from random import *
from time import perf_counter

import numpy as np
import pandas as pd
from django import db
from django.conf import settings
from django.db.models import Avg
from fuzzyset import FuzzySet
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from range_key_dict import RangeKeyDict
from simple_salesforce import Salesforce
from tablib import Dataset

import dedupper.threads
from dedupper.models import repContact, sfcontact, dedupTime, duplifyTime, uploadTime, progress
from dedupper.resources import RepContactResource, SFContactResource
import jellyfish as jelly
import recordlinkage as rl
from recordlinkage.preprocessing import clean, phonenumbers, phonetic
from recordlinkage.index import Full, Block


def preprocess(sfdf, repdf):
    print('enter PREPROCESS')

    global key_list, keys
    '''preprocessing'''

    sfdf.update(clean(sfdf.FirstName))
    sfdf.update(clean(sfdf.LastName))
    sfdf.update(clean(sfdf.Email))
    sfdf.update(clean(sfdf.State))
    sfdf.update(phonenumbers(sfdf.Zip))
    sfdf.update(clean(sfdf.City))
    sfdf.update(phonenumbers(sfdf.Phone))
    sfdf.update(clean(sfdf.CRD.astype(str)))

    repdf.update(clean(repdf.FirstName))
    repdf.update(clean(repdf.LastName))
    repdf.update(clean(repdf.Email))
    repdf.update(clean(repdf.State))
    repdf.update(phonenumbers(repdf.Zip))
    repdf.update(clean(repdf.City))
    repdf.update(phonenumbers(repdf.Phone))
    repdf.update(clean(repdf.CRD.astype(str)))

    '''key generating'''

    for df in [sfdf, repdf]:
        for key in keys:
            if len(key) > 1:
                key_col = ''.join([''.join(c for c in s if c.isupper()) for s in key])
                if key_col not in key_list:
                    key_list.append(key_col)
                df[key_col] = pd.Series(np.add.reduce(df[key].astype(str), axis=1))
            else:
                if key[0] not in key_list:
                    key_list.append(key[0])
    print('exit PREPROCESS')

def match_crds(sfdf, repdf):
    print('enter CRD MATCH')
    global lt_ID_update_list
    sfcrd = set(sfdf.CRD)
    repcrd = list(repdf.CRD)
    print(len(sfcrd), len(repcrd))

    #find intersection of CRD
    CRD_matches = set(sfcrd).intersection(set(repcrd))
    lt_ID_update_list = [np.nan for _ in repcrd]

    #match those records
    for crd in CRD_matches:
        lt_ID_update_list[repdf[repdf.CRD == crd].iloc[0].name] = sfdf[sfdf.CRD==crd].iloc[0]["Id"]
    print('exit CRD MATCH')

def dedupe_ai():
    preprocess(sfdf, ltdf)
    match_crds(sfdf, ltdf)
    ltgroups = ltdf.groupby('LastName')
    sfgroups = sfdf.groupby('LastName')  # index using groups by lastname
    lt_lastnames = list(set(ltgroups.groups.keys()))
    sf_lastnames = list(set(sfgroups.groups.keys()))
    last_name_groups = list(set(lt_lastnames).intersection(sf_lastnames))
    matched = False
    manual_dict = dict()
    start = pc()
    for ln in last_name_groups:
        for index in ltgroups.groups[ln]:
            if not lt_ID_update_list[index] == np.nan:
                # only do indexes that have not already been populated in the lt_ID_update_list
                matched = False
                for key in key_list:
                    sf_keys = [sfdf.iloc[i][key] for i in sfgroups.groups[ln]]
                    # swap out with fuzzyset algorithm
                    # fuzzyset_alg
                    # possibilities = process.extract(ltdf.iloc[index][key], sf_keys, limit=3, scorer=jelly.jaro_winkler)
                    possibilities = fuzzyset_alg(ltdf.iloc[index][key], sf_keys)
                    manuals = [possible[0] for i, possible in enumerate(possibilities) if 95 <= possible[1] < 97]
                    non_match = [possible[0] for i, possible in enumerate(possibilities) if possible[1] < 95]
                    if possibilities and possibilities[0][1] >= 97:
                        lt_ID_update_list[index] = sfdf[sfdf[key] == possibilities[0][0]].iloc[0]['Id']
                        matched = True
                        break
                    elif manuals:
                        manual_dict[index] = [i for i in sfgroups.groups[ln] if sfdf.iloc[i][key] in manuals]
                        lt_ID_update_list[index] = 'manual'
                        print('manual check')
                        matched = True
                        break
    #             if not matched:
    #                 print(f"NEW {key} ({ltdf.iloc[index]['FirstName']} {ltdf.iloc[index]['LastName']}): {[ (sfdf[sfdf[key] == pos ].iloc[0]['FirstName'] ,sfdf[sfdf[key] == pos ].iloc[0]['LastName'] ) for pos in non_match]}")
    #             else:
    #                 matched=False
    print(f'time: {pc() - start}')