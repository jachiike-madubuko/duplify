import pandas as pd
from dupandas import Dedupe
from simple_salesforce import Salesforce


def run():
    dupe = Dedupe()

    query = "select Id, CRD__c, FirstName, LastName, Suffix, MailingStreet, MailingCity, MailingState, MailingPostalCode, Phone, MobilePhone, HomePhone, otherPhone, Email, Other_Email__c, Personal_Email__c   from Contact where Territory_Type__c='Geography' and Territory__r.Name like "
    starts_with = f"'RC%'"
    sf = Salesforce(password='7924trill', username='jmadubuko@wealthvest.com',
                    security_token='W4ItPbGFZHssUcJBCZlw2t9p2')

    territory = sf.bulk.Contact.query(query + starts_with)
    territory = pd.DataFrame(territory).drop('attributes', axis=1).replace([None], [''], regex=True)
    clean_config = {'lower': True, 'punctuation': True, 'whitespace': True, 'digit': True}
    match_config = {'exact': False, 'levenshtein': True, 'soundex': False, 'nysiis': False}

    dupe = Dedupe(clean_config=clean_config, match_config=match_config)
    input_config = {
        'input_data' : territory,
       '_id': territory['Id'].name,
        'columns' : territory['CRD__c']
        }
    results = dupe.dedupe(input_config)
    return results


