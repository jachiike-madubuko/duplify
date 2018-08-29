
import pandas as pd
from random import randint
import numpy as np
import datetime
usage_map=usage_df=sf_contact_by_type=None

sf_contact_df = pd.read_hdf('contacts/panda_pickles/contact.h5')


def contacts_clean_up(threshold, num_records=12):
    record_types = ['WS','BD','P','WV',]
    api_names = ['marketo', 'afmo', 'old shit', 'dumb shit']
    print('create pandas map')
    df_map= contacts_using_fields_in_criteria(int(threshold), int(num_records))
    api_names = list(df_map.keys())
    record_types = list(df_map[api_names[0]])
    return api_names, record_types

def get_resampled_field_count(table):
    #index the contacts with last act, last mod, and created data
    #for each resample contacts by month then get count
    #{ 'date field' : table.resample('M').count() }
    data =  {}
    return data

def fieldsByThreshold(df,up_percent, low_percent=0):
    #percentage of the fields usage in SF
    total_usage_per_col = df.count()/len(df);
    return total_usage_per_col[ total_usage_per_col.between(low_percent/100,up_percent/100)]

sf_contact_by_type = {i: sf_contact_df[sf_contact_df['RECORD_TYPE_NAME__C'] == i] for i in
                          sf_contact_df.RECORD_TYPE_NAME__C.unique()}

    # fields usage per record type
usage_map = {i: fieldsByThreshold(sf_contact_by_type[i], 101) for i in
                           sf_contact_df.RECORD_TYPE_NAME__C.unique()}

usage_df = pd.DataFrame(usage_map)

usage_df.to_pickle('contacts/panda_pickles/usage.pkl')

def threshold_per_type(max_threshold,  min_num_types):
    # example -> threshold_per_type(1,12)  all fields that have under 1% usage for 12 or more record types
    all_fields = list(usage_df.index)

    fields = [i for i in all_fields if
              len([j for j in list(usage_df.loc[i] <= max_threshold / 100) if j == True]) >= min_num_types]
    return usage_df.loc[fields]  # all the fields that fall under 'threshold' usage 'cnt' times


def contact_type_using_field(record_type, field_name):
    if record_type == 'All':
        contacts = sf_contact_df
    else:
        contacts = sf_contact_by_type[record_type]

    return contacts[contacts[field_name].notnull()]

# get contacts using under used fields
def contacts_using_fields_in_criteria(thresh_percent, num_types):

    types = list(usage_df.columns)
    types.append('All')
    # fields that fit the criteria
    fields_in_threshold = list(threshold_per_type(thresh_percent, num_types).index)
    # dictionary containing each field in the criteria and the contacts using that field for each record type
    return {i: {j: contact_type_using_field(j, i) for j in types} for i in fields_in_threshold}

def date_range_of_contacts(df):
    earliest = df.resample('M').count()[:1].index.date[0].isoformat()
    latest = df.resample('M').count()[-1:].index.date[0].isoformat()
    return f'from {earliest} to {latest}'
