
# coding: utf-8




from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import pandas as pd
from time import sleep
from simple_salesforce import Salesforce
import json
from fuzzywuzzy import fuzz
from random import randint
from functools import reduce
from collections import defaultdict
import datetime
browser = None
#query contacts
# query = f"select Id, CRD__c, Name, Middle_Name__c, MailingStreet, MailingCity, MailingState, MailingPostalCode, Finra_BrokerCheck__c, Broker_Dealer__r.Firm_CRD__c , Broker_Dealer__r.Name from Contact where Broker_Dealer__r.Firm_CRD__c != null  limit 100"

# contacts = sf.bulk.Contact.query(query)
# len(contacts)





# ids = [i['Id'] for i in contacts]   #list of contactIDs
# crds = [i['CRD__c'] for i in contacts]   #list of CRDs





#screen_scraper for non_crd contacts
def screen_scraper(crd_list):
    #scrape the finra brokercheck website
    #dict of finra data
    data = defaultdict(list)

    #data selectors
    name_selector     = '#bio-geo-summary > div.names.layout-xs-column.layout-column.flex-auto > div.namesummary.flex-noshrink.gutter-right.layout-wrap.ng-binding'
    alt_name_selctor  = '#bio-geo-summary > div.names.layout-xs-column.layout-column.flex-auto > div:nth-child(2) > div'
    alt_name_selctor2 = '#bio-geo-summary > div.names.layout-xs-column.layout-column.flex-auto > div:nth-child(3) > div'
    firm_selector     = '#bio-geo-summary > div.layout-xs-column.layout-row.flex-auto > div.employment.md-body-1.offset-margintop-1x.layout-align-start-start.layout-row.flex-offset-gt-xs-5.flex-gt-xs-25.flex > div.font-dark-gray.ng-scope.flex > div.bold.ng-binding'
    firmCRD_selector  = '#bio-geo-summary > div.layout-xs-column.layout-row.flex-auto > div.employment.md-body-1.offset-margintop-1x.layout-align-start-start.layout-row.flex-offset-gt-xs-5.flex-gt-xs-25.flex > div.font-dark-gray.ng-scope.flex > div:nth-child(2) > span.ng-binding'
    address1_selector = '#bio-geo-summary > div.layout-xs-column.layout-row.flex-auto > div.employment.md-body-1.offset-margintop-1x.layout-align-start-start.layout-row.flex-offset-gt-xs-5.flex-gt-xs-25.flex > div.font-dark-gray.ng-scope.flex > div:nth-child(3) > div:nth-child(1) > span:nth-child(1)'
    address2_selector = '#bio-geo-summary > div.layout-xs-column.layout-row.flex-auto > div.employment.md-body-1.offset-margintop-1x.layout-align-start-start.layout-row.flex-offset-gt-xs-5.flex-gt-xs-25.flex > div.font-dark-gray.ng-scope.flex > div:nth-child(3) > div:nth-child(1) > span:nth-child(2)'
    city_selector     = '#bio-geo-summary > div.layout-xs-column.layout-row.flex-auto > div.employment.md-body-1.offset-margintop-1x.layout-align-start-start.layout-row.flex-offset-gt-xs-5.flex-gt-xs-25.flex > div.font-dark-gray.ng-scope.flex > div:nth-child(3) > div:nth-child(2) > span:nth-child(1)'
    st_selector       = '#bio-geo-summary > div.layout-xs-column.layout-row.flex-auto > div.employment.md-body-1.offset-margintop-1x.layout-align-start-start.layout-row.flex-offset-gt-xs-5.flex-gt-xs-25.flex > div.font-dark-gray.ng-scope.flex > div:nth-child(3) > div:nth-child(2) > span:nth-child(3)'
    zip_selector      = '#bio-geo-summary > div.layout-xs-column.layout-row.flex-auto > div.employment.md-body-1.offset-margintop-1x.layout-align-start-start.layout-row.flex-offset-gt-xs-5.flex-gt-xs-25.flex > div.font-dark-gray.ng-scope.flex > div:nth-child(3) > div:nth-child(2) > span:nth-child(4)'
    show_more_selector= '#bio-geo-summary > div.names.layout-xs-column.layout-column.flex-auto > div.namesummary.flex-noshrink.gutter-right.layout-wrap.ng-binding > span > span'

    #loop through crds and scrape
    for crd in crd_list:
        browser.get(f'https://brokercheck.finra.org/individual/summary/{crd}')
        sleep(1)
        if 'BrokerCheck' in browser.title[:12]: #main BrokerCheck page
            browser.quit()
            continue
        meta       = browser.find_elements_by_css_selector('head > meta:nth-child(27)')
        if len(meta) == 0:
            browser.quit()
            continue
        if 'was previously registered as a broker.' in meta[0].get_attribute('content'):
            browser.quit()
            continue
        not_registered_selector = '#bio-geo-summary > div.layout-xs-column.layout-row.flex-auto > div.employment.md-body-1.offset-margintop-1x.layout-align-start-start.layout-row.flex-offset-gt-xs-5.flex-gt-xs-25.flex > div > div > span'
        if len(browser.find_elements_by_css_selector(not_registered_selector)) > 1 and 'Not currently' in browser.find_elements_by_css_selector(not_registered_selector)[0].text :
            browser.quit()
            continue
        #get data
        name       = browser.find_element_by_css_selector(name_selector)
        firm       = browser.find_element_by_css_selector(firm_selector)
        firmCRD    = browser.find_element_by_css_selector(firmCRD_selector)
        address1   = browser.find_element_by_css_selector(address1_selector)
        address2   = browser.find_element_by_css_selector(address2_selector)
        city       = browser.find_element_by_css_selector(city_selector)
        st         = browser.find_element_by_css_selector(st_selector)
        zip_postal = browser.find_element_by_css_selector(zip_selector)
        alt_names = browser.find_elements_by_css_selector(alt_name_selctor)
        #check for alternate names
        if len(alt_names) > 0:
            #check for multiple alternate names
            if '...' in alt_names[0].text:
                browser.find_element_by_css_selector(show_more_selector).click()
                alt_names = browser.find_element_by_css_selector(alt_name_selctor2).text.replace('(','').replace(')','')
            else:
                alt_names = browser.find_element_by_css_selector(alt_name_selctor).text.replace('(','').replace(')','')

        #retry if element wasn't ready when first selected
        if firm.text == '':
            firm = browser.find_element_by_css_selector(firm_selector)
        if firmCRD.text == '':
            firmCRD = browser.find_element_by_css_selector(firmCRD_selector)
        if address1.text == '':
            address1 = browser.find_element_by_css_selector(address1_selector)
        if address2.text == '':
            address2 = browser.find_element_by_css_selector(address2_selector)
        if city.text == '':
            city = browser.find_element_by_css_selector(city_selector)
        if st.text == '':
            st = browser.find_element_by_css_selector(st_selector)
        if zip_postal.text == '':
            zip_postal = browser.find_element_by_css_selector(zip_selector)

        #store data
        data['Firm'].append(firm.text)
        data['Firm CRD'].append(firmCRD.text)
        data['Name'].append(name.text)
        data['Alt Names'].append(alt_names)
        data['CRD'].append(crd)
        data['Street'].append( f'{address1.text} {address2.text}')
        data['City'].append(city.text)
        data['State'].append(st.text)
        data['Zip'].append(zip_postal.text)

        browser.quit()
    for i in data.values():
        if len(i) < 1:
            return None
    return data

def save_scrape(name, data):
    df = pd.DataFrame(data)
    now = datetime.datetime.now().ctime()
    df.to_csv(f'{name} - {now}.csv', index='contactID')

#determine if names match
def name_check(finra_name, alt_finra_names, sf_name):
    alt_name_list = []
    finra_name= finra_name.replace('.', '')
    sf_name= sf_name.replace('.', '')
    #checks for match ignoring order of names
    sf_set = set(sf_name.lower().split(' '))
    finra_set = set(finra_name.lower().split(' '))

    if sf_set.issubset(finra_set) or finra_set.issubset(sf_set):
        return True
    #parse the alternate names into a list
    if type(alt_finra_names) != list:
        alt_name_list = alt_finra_names.split(',')
    #loop through alternate names for a match
    if len(alt_name_list) > 0:
        for alt_name in alt_name_list:
            alt_set = set(alt_name.lower().replace('.', '').split(' '))
            if sf_set.issubset(alt_set) or alt_set.issubset(sf_set):
                return True
    return False

def street_check(finra_street, sf_street):
    streets = []
    #convert street endings
    for i in [finra_street, sf_street]:
        i = i.lower()
        i = i.replace('avenue', 'ave')
        i = i.replace('suite', 'ste')
        i = i.replace('boulevard', 'blvd')
        i = i.replace('apartment', 'apt')
        i = i.replace('street', 'st')
        i = i.replace('drive', 'dr')
        i = i.replace('road', 'rd')
        i = i.replace('court', 'ct')
        i = i.replace('lane', 'ln')
        i = i.replace('trail', 'trl')
        i = i.replace('circle', 'cir')
        i = i.replace('parkway', 'pkwy')
        i = i.replace('north', 'n')
        i = i.replace('south', 's')
        i = i.replace('west', 'w')
        i = i.replace('east', 'e')
        i = i.replace('.', '')
        i = i.replace('#', '')
        i = i.replace(',', '')
        street_set = set(i.split(' '))
        streets.append(street_set)

    if streets[0].issubset(streets[1]) or streets[1].issubset(streets[0]) :
        return True
    else:
        return False

#cross check salesforce data with FINRABROKERCHECK
def finra_check(contact):
    is_up_to_date = False
    if contact['CRD__c']:

        #searching FINRA for contact with CRD:
        finra_data = screen_scraper([contact['CRD__c']])
        if not finra_data:
            return [contact['Id']], [False], ['Contact not registered as Broker']
#         print('________FINRA_______')
#         print(finra_data)
#         print('_______SALES FORCE________')
#         print(json.dumps(contact, indent=2))

#         #check for middle name
        if contact['Middle_Name__c']:
            name = contact['Name']+ ' ' +contact['Middle_Name__c']
        else:
            name =  contact['Name']

        #create flags for data and append to the end of finra data list
        try:
            finra_data['Name'].append(name_check(finra_data['Name'][0], finra_data['Alt Names'][0], name))

            finra_data['State'].append(contact['MailingState'].lower() == finra_data['State'][0].lower())
            finra_data['City'].append(contact['MailingCity'].lower()  == finra_data['City'][0].lower())
            finra_data['Zip'].append(contact['MailingPostalCode'][:5].lower()  == finra_data['Zip'][0][:5].lower())
            finra_data['Street'].append(street_check(contact['MailingStreet']  , finra_data['Street'][0]))

            finra_data['Firm'].append(contact['Broker_Dealer__r']['Name'].replace('.','').replace(',','').lower()  == finra_data['Firm'][0].replace('.','').replace(',','').lower())
            finra_data['Firm CRD'].append(contact['Broker_Dealer__r']['Firm_CRD__c'].lower() == finra_data['Firm CRD'][0].lower())

    #         print(f"Name Match: {finra_data['Name'][1]} => {[finra_data['Name'][0], name]}")
    #         print(f"BD Match: {finra_data['Firm'][1]} => {[contact['Broker_Dealer__r']['Name'], finra_data['Firm'][0]]}")
    #         print(f"BD CRD Match: {finra_data['Firm CRD'][1]} => {[contact['Broker_Dealer__r']['Firm_CRD__c'] , finra_data['Firm CRD'][0]]}")
    #         print(f"Street Match: {finra_data['Street'][1]} => {[contact['MailingStreet']  , finra_data['Street'][0]]}")
    #         print(f"City Match: {finra_data['City'][1]} => {[contact['MailingCity'], finra_data['City'][0]]}")
    #         print(f"State Match: {finra_data['State'][1]} => {[contact['MailingState'] , finra_data['State'][0]]}")
    #         print(f"Zip Match: {finra_data['Zip'][1]} => {[contact['MailingPostalCode']  , finra_data['Zip'][0]]}")
    #         print('---------'.rjust(50))
            #reduce the boolean flags using the "and" operator
            is_up_to_date = reduce((lambda x,y: x&y), [i[1] for i in list(finra_data.values()) if len(i) > 1])

            finra_2_sf_fields = {
                'Name' : 'Name',
                'State' : 'MailingState',
                'City' : 'MailingCity',
                'Street' : 'MailingStreet',
                'Firm' : 'Broker_Dealer__r.Name',
                'Firm CRD' : 'Broker_Dealer__r.Firm_CRD__c',
                'Zip' : 'MailingPostalCode',
            }

            #report FINRA DATA for field if not matching
            report = {finra_2_sf_fields[i] : finra_data[i][0] for i in finra_2_sf_fields.keys() if not finra_data[i][1]}
            report = json.dumps(report, separators=(',',':'))
            if report == '{}':
                report = 'Salesforce Contact is up to date with Finra Broker Check'
            return [contact['Id']], [is_up_to_date], [report]
        except :
            return [contact['Id']], [False], ['Connection error']

    else:
        return [contact['Id']], [False], ['No CRD']


def finra_results(title, contacts):
    results = defaultdict(list)
    for contact in contacts:
        contact_id, matched, report = finra_check(contact)
        results['contactID'].append(*contact_id)
        results['Finra Match'].append(*matched)
        results['Fields'].append(*report)
    save_scrape(title, results)


def finra_check_job(filter_args):
    globals()['browser'] =  webdriver.Chrome()
    sf = Salesforce(password='7924Trill!', username='jmadubuko@wealthvest.com', organizationId='00D36000001DkQo')

    select_contacts = 'select Id, CRD__c, Name, Middle_Name__c, MailingStreet, MailingCity, MailingState, MailingPostalCode, Finra_BrokerCheck__c, Broker_Dealer__r.Firm_CRD__c , Broker_Dealer__r.Name from Contact'
    results = defaultdict(list)
    if filter_args['All']:
        print('querying all')
        query = select_contacts + f" CRD__c != null and where Broker_Dealer__r.Firm_CRD__c != null limit 10"
        contacts = sf.bulk.Contact.query(query)
        print(f'Number of Contacts:{len(contacts)}')
        finra_results('All Contacts FinraCheck', contacts)

    elif filter_args['Channel']:
        print(f"querying the {filter_args['Channel']} Channel")
        channel = f"'{filter_args['Channel']}%'"
        q_filter = " where CRD__c != null and Broker_Dealer__r.Firm_CRD__c != null and Territory_Type__c = 'Geography' and Territory__r.Name like "
        query = select_contacts + q_filter + channel
        contacts = sf.bulk.Contact.query(query)
        print(f'{filter_args["Channel"]}:{len(contacts)}')
        finra_results(f'{filter_args["Channel"]} FinraCheck', contacts)

    elif filter_args['Group']:
        print(f"querying {len(filter_args['Group'])} contacts")
        query = select_contacts + f" where Broker_Dealer__r.Firm_CRD__c != null and Id in {filter_args['Group']}"
        contacts = sf.bulk.Contact.query(query)
        print(f'Group Size:{len(contacts)}')
        finra_results('Custom FinraCheck', contacts)

    elif filter_args['Individual']:
        query = select_contacts + f" where Id='{filter_args['Individual']}'"
        contacts = sf.bulk.Contact.query(query)
        results['contactID'], results['Finra Match'], results['Fields'] = finra_check(contacts[0])
        return pd.DataFrame(results)
        # save_scrape('Individual FinraCheck', results)

    else: return 'could not perform finra check'
# #test finra_check_job::All
# job = defaultdict(int)
# job['All'] = True
# finra_check_job(job)

def finra_channel(channel):
    job = defaultdict(int)
    finra_check_job(job)

def finra_contact(contactID):
    job = defaultdict(int)
    return finra_check_job(job)

def finra_report_job(CRDs):
    data = screen_scraper(CRDs)
    for n,i in enumerate(data['Alt Names']):
        if i == []:
            data['Alt Names'][n]= ''
    save_scrape('Finra Report', data)# finra_report_job(crds[:10])





#build visualforce page to do call outs to code for each mode
#start in jdev, create contacts with valid CRDs and Broker Dealers
#create bottle server in spyder to service the code

