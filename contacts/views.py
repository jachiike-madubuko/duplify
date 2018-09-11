from django.shortcuts import render
from contacts.utils  import contacts_clean_up, get_resampled_field_count, contact_type_using_field
from collections import defaultdict
from django.http import HttpResponse, JsonResponse
import pandas as pd

# Create your views here.
#TODO load in contacts.csv and convert df into fields by usage

def index(request):

    print('contacts')
    return render(request, 'contacts/index.html')

def contacts(request):

    data = defaultdict(int)
    if request.method == 'GET':

        threshold = request.GET.get('threshold')
        if 'num_records' in request.GET:
            num_record_types = request.GET.get('num_records')
            data['api_names'], data['record_types'] = contacts_clean_up(threshold, num_record_types)
        else:
            data['api_names'], data['record_types'] = contacts_clean_up(threshold)
        print(data)

        return JsonResponse(data, safe=False)

def leads(request):

    data = defaultdict(int)
    if request.method == 'GET':

        threshold = request.GET.get('threshold')
        if 'num_records' in request.GET:
            num_record_types = request.GET.get('num_records')
            data['api_names'], data['record_types'] = contacts_clean_up(threshold, num_record_types)
        else:
            data['api_names'], data['record_types'] = contacts_clean_up(threshold)
        print(data)

        return JsonResponse(data, safe=False)

def table(request):
    api_name = request.GET.get('api_key')
    record_type = request.GET.get('type_key')
    print(api_name, record_type)
    table = contact_type_using_field(record_type, api_name)
    return JsonResponse({'table':table.to_html()}, safe=False)

def plotly(request):
    '''
    For contact info, let the data tell the story,
	for each table of contacts, deploy a plotly interface with the contacts resampled by month for created by, last activity, and last modified
    :param request:
    :param api_name: str
    :param record_type: str

    :return plotly: data for plotly.js => resampled(count) by month for created by, last activity, and last modified
    '''
    api_name = request.GET.get('api_key')
    record_type = request.GET.get('type_key')
    table = pd.read_pickle(f'contacts/panda_pickles/{api_name}-{record_type}.pkl')
    data = get_resampled_field_count(table)


    return JsonResponse({'table':'plot.to_html()'}, safe=False)
