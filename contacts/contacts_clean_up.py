
import pandas as pd
from random import randint


def contacts_clean_up(threshold, num_records=12):
    record_types = ['WS','BD','P','WV',]
    api_names = ['marketo', 'afmo', 'old shit', 'dumb shit']
    print('create pandas map')
    df_map  = {
        api_name :  {
            record_type :
                pd.DataFrame({
                    'contact'+str(i): [i*i for fields in range(12)] for i in range(randint(28,100))
                })
            for record_type in record_types
        }
        for api_name in api_names
    }
    api_names = list(df_map.keys())
    record_types = list(df_map[api_names[0]])
    print('create pandas pickle')
    for api_name in api_names:
        for record_type in record_types:
            df_map[api_name][record_type].to_pickle(f'contacts/panda_pickles/{api_name}-{record_type}.pkl')

    return api_names, record_types


def get_resampled_field_count(table):
    #index the contacts with last act, last mod, and created data
    #for each resample contacts by month then get count
    #{ 'date field' : table.resample('M').count() }
    data =  {}
    return data