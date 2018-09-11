from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pandas  as pd
from tablib import Dataset
from collections import defaultdict
from scraper.scraper import finra_check_job, fuzz_comp
import csv, time
import logging
from uuid import uuid4
import requests
from functools import reduce

from simple_salesforce import Salesforce

#connect scrapyd
# scrapyd = ScrapydAPI('http://localhost:6800')
# Create your views here.

def index(request):
    print('scrape')
    return render(request, 'scraper/index.html')

@csrf_exempt
def scrape(request):
    #apex callout sends json data with group, indi, and channel attrs if not filled then = 0

    print(request.GET)
    logging.debug(request.GET)

    export = finra_check_job(request.GET)


    print('run scraper')
    print('get results from scraper')
    filename = 'filename="Scraper.csv"'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; ' + filename
    dataset = Dataset()
    dataset.csv = export.to_csv(index=False)

    writer = csv.writer(response)
    for line in dataset:
        writer.writerow(line)

    return response

# @csrf_exempt
# def crawl(request):
#     if request.method == 'GET':
#         contactIDs = request.GET.get('IDs', None)
#
#     contactIDs = contactIDs.split('-')
#
#
#     u_id = str(uuid4())
#
#
#     #setting for scrapy spider
#     settings = {
#         'unique_id': u_id,
#         'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
#         'STATSMAILER_RCPTS': ['jachiike.madubuko@gmail.com'],
#         'MEMUSAGE_NOTIFY_MAIL': ['jachiike.madubuko@gmail.com'],
#         'ROBOTSTXT_OBEY': True,
#         'DOWNLOAD_DELAY': 0.5,
#         'AUTOTHROTTLE_ENABLED': True,
#     }
#
#     #schedule crawling task, return task and store in cache
#     task = scrapyd.schedule('default',
#                             'fincrawler',
#                             settings=settings,
#                             start_urls = [])

#return time and # finra checks performed
def fbc(request):
    select_contacts = 'select Id, CRD__c, Name, Middle_Name__c, MailingStreet, MailingCity, MailingState, MailingPostalCode, Finra_BrokerCheck__c, Broker_Dealer__r.Firm_CRD__c , Broker_Dealer__r.Name from Contact'

    if request.method == 'GET':
        contact_IDs = request.GET.get('IDs', None)
        contact_ID = request.GET.get('ID', None)
        contact_channel = request.GET.get('channel', None)
        all_contacts = request.GET.get('all', None)

    # contactIDs = contactIDs.split('-')

    # contactID = '0033600001cTxkx'
    # sf = Salesforce(password='7924Trill!', username='jmadubuko@wealthvest.com', organizationId='00D36000001DkQo')
    # query = select_contacts + f" where Id = '{contactID}'"
    # # query = select_contacts + f" where Broker_Dealer__r.Firm_CRD__c != null and CRD__c != null and Id in {contactIDs}"
    # contacts = sf.bulk.Contact.query(query)

    finra_sf_map = {
            'CRD__c': ['sourceID'],
            'firstName':[ 'firstName'],
            'Middle_Name__c': ['middleName'],
            'lastName':['lastName'],
            'mailingStreet': ['currentEmployments', 0, 'address', 'street'],
            'MailingCity': ['currentEmployments', 0, 'address', 'city'],
            'MailingPostalCode':  ['currentEmployments', 0, 'address', 'zip'],
            'MailingState':  ['currentEmployments', 0, 'address', 'state'],
            'Broker_Dealer__r.Firm_CRD__c': ['currentEmployments', 0, 'firmId'],
        }
    sf_contact = {
            'Id': '0033600001cTxkx',
            'CRD__c': '5155663',
            'firstName': 'Patrick',
            'Middle_Name__c': '',
            'lastName':'Gray',
            'mailingStreet': '1055 Lpl Way',
            'MailingCity': 'Fort Mill',
            'MailingState': 'SC',
            'MailingPostalCode': '29715',
            'Broker_Dealer__r' : {
                'Firm_CRD__c': '6413',
            }
        }
    contact_IDs = '.'
    if contact_ID:

        # crds = [contact['CRD__c'] for contact in contacts]

        crd = 5155663
        response = requests.get('https://fbc-wv.herokuapp.com/fbc/', params={'crd': int(sf_contact['CRD__c'])})
        finra_contact = response.json()

        fields_bools = [ ]
        for sf, finra in finra_sf_map.items():
            if len(finra) == 1:
                f= finra_contact[finra[0]]
            elif len(finra) == 3:
                f= finra_contact[finra[0]][finra[1]][finra[2]]
            else:
                f=finra_contact[finra[0]][finra[1]][finra[2]][finra[3]]
            if '.' in sf:
                idx = sf.split('.')
                s= sf_contact[idx[0]][idx[1]]
            else:
                s = sf_contact[sf]

            if s and f:
                fields_bools.append(fuzz_comp(s,f))

        matched = reduce(lambda a, b: a & b, fields_bools)
        return JsonResponse({sf_contact['Id'] : matched}, safe=False)

    if contact_IDs:
        results = {}
        t1 = time.time()

        for i in [5155663, 3006258, 5155663, 5155663]:
            response = requests.get('https://fbc-wv.herokuapp.com/fbc/', params={'crd': i})
            finra_contact = response.json()

            fields_bools = []
            for sf, finra in finra_sf_map.items():
                if len(finra) == 1:
                    f = finra_contact[finra[0]]
                elif len(finra) == 3:
                    f = finra_contact[finra[0]][finra[1]][finra[2]]
                else:
                    f = finra_contact[finra[0]][finra[1]][finra[2]][finra[3]]
                if '.' in sf:
                    idx = sf.split('.')
                    s = sf_contact[idx[0]][idx[1]]
                else:
                    s = sf_contact[sf]

                if s and f:
                    fields_bools.append(fuzz_comp(s, f))

            results[i] = reduce(lambda a, b: a & b, fields_bools)
        return JsonResponse(results, safe=False)








