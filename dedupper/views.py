from django.shortcuts import render
from django.views.generic import TemplateView, ListView
import django_tables2
from dedupper.models import dedupTime, duplifyTime, uploadTime,  sfcontact, repContact, progress
from  dedupper.filters import SimpleFilter
from dedupper.tables import StatsTable, ContactTable, RepContactTable
from tablib import Dataset
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from dedupper.forms import UploadFileForm
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin, RequestConfig
from django.core.management import call_command
from dedupper.resources import RepContactResource, SFContactResource, DedupTimeResource, DuplifyTimeResource, UploadTimeResource
from  dedupper.utils import *
import csv
import json
import pickle
from django.conf import settings
from difflib import SequenceMatcher as SeqMat
'''
#TODO change the HTTP request 
timeout for the running algorithm or 
have a middle man page that loads and send an request for 
TODO set up postgresql
#TODO https://medium.com/@johngrant/django-and-heroku-postgres-databases-6c22ffd71081 
https://medium.com/agatha-codes/9-straightforward-steps-for-deploying-your-django-app-with-heroku-82b952652fb4
http://www.marinamele.com/2013/12/how-to-set-django-app-on-heroku-part-i.html
https://www.youtube.com/watch?v=P8_wDttTeuk
'''
keys= []

def display(request):

    config = RequestConfig(request, paginate={'per_page': 1000})
    undecided_table = RepContactTable(repContact.objects.filter(type__exact='Undecided'), prefix='U-')  # prefix specified
    duplicate_table = RepContactTable(repContact.objects.filter(type__exact='Duplicate'), prefix='D-')  # prefix specified
    new_record_table = RepContactTable(repContact.objects.filter(type__exact='New Record'), prefix='N-')  # prefix
    manual_check_table = RepContactTable(repContact.objects.filter(type__exact='Manual Check'), prefix='M-')  # prefix
    # specified
    config.configure(undecided_table)
    config.configure(duplicate_table)
    config.configure(new_record_table)
    config.configure(manual_check_table)

    undecided = RepContactResource().export(repContact.objects.filter(type='Undecided'))
    newRecord = RepContactResource().export(repContact.objects.filter(type='New Record'))
    duplicate = RepContactResource().export(repContact.objects.filter(type='Duplicate'))
    manual_check = RepContactResource().export(repContact.objects.filter(type='Manual Check'))

    return render(request, 'dedupper/sorted.html', {
        'undecided_table': undecided_table,
        'duplicate_table': duplicate_table,
        'new_record_table': new_record_table,
        'manual_check_table': manual_check_table,
    })

def download(request,type):
    fields = ('SF link', 'id','CRD', 'First', 'Last', 'Street', 'City',
              'State', 'Zip', 'Phone', 'Home Phone', 'Mobile Phone',
              'Other Phone', 'Work Email', 'Personal Email', 'Other Email', 'Match Score', 'Key' )

    if(type == "Duplicate"):
        filename = 'filename="Duplicates.csv"'
    elif(type == "NewRecord"):
        filename = 'filename="New Records.csv"'
        type = 'New Record'
    elif(type == "ManualCheck"):
        filename = 'filename="Manual Checks.csv"'
        type = 'Manual Check'
    else:
        filename = 'filename="Undecided Records.csv"'

    rep_resource = RepContactResource()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; '+filename

    writer = csv.writer(response)
    writer.writerow(fields)

    users = repContact.objects.filter(type = type)
    dataset = rep_resource.export(users)
    for line in dataset:
        writer.writerow(line)

    return response

def download_times(request,type):
    if(type == "DD"):
        filename = 'filename="Dedup Times.csv"'
        times = dedupTime.objects.all().values_list()
        export_headers = [i.name for i in dedupTime._meta.local_concrete_fields]
    elif(type == "D"):
        filename = 'filename="Duplify Times.csv"'
        times = duplifyTime.objects.all().values_list()
        export_headers = [i.name for i in duplifyTime._meta.local_concrete_fields]
    else:
        filename = 'filename="Upload Times.csv"'
        times = uploadTime.objects.all().values_list()
        export_headers = [i.name for i in uploadTime._meta.local_concrete_fields]


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; '+filename
    writer = csv.writer(response)
    writer.writerow(export_headers)

    for time in times:
        writer.writerow(time)

    return response

def duplify(request):
    if request.method == 'GET':
        keylist = request.GET.get('keylist')
        print('Starting algorithm with {}'.format(keylist))
        keylist = keylist.split("_")
        partslist = [i.split('-') for i in keylist[:-1]]
        result = key_generator.delay(partslist)

    return JsonResponse({'task_id': result.task_id}, safe=False)

def flush_db(request):
    call_command('flush', interactive=False)
    return redirect('/')

def import_csv(request):
    repcontact_resource = RepContactResource()
    sfcontact_resource = SFContactResource()
    if request.method == 'GET':
        sf_header_map = request.GET.get('sf_map')
        rep_header_map = request.GET.get('rep_map')

        sf_header_map = json.loads(sf_header_map)
        rep_header_map = json.loads(rep_header_map)

        with open(settings.REP_CSV, 'rb') as file:
            pd_rep_csv =pickle.load(file)
            print('pickle load reps')

        with open(settings.SF_CSV, 'rb') as file:
            pd_sf_csv = pickle.load(file)
            print('pickle load sf')

        load_csv2db(pd_rep_csv, rep_header_map, repcontact_resource)
        load_csv2db(pd_sf_csv, sf_header_map, sfcontact_resource, file_type='SF')


    return JsonResponse({'msg': 'success!'}, safe=False)

def index(request):
    return render(request, 'dedupper/rep_list_upload.html')

def key_gen(request):
    try:
        key = make_keys([i.name for i in repContact._meta.local_fields])
    except:
        key = [('error', 100, 0, 100, 0, 100)]
    return render(request, 'dedupper/key_generator.html', {'keys': key})

def map(request):
    exclude = ('id', 'average', 'type', 'closest1_contactID', 'closest1', 'closest2_contactID', 'closest2', 'closest3_contactID', 'closest3', 'dupFlag', 'keySortedBy', 'closest_rep')
    rep_key = [i.name for i in repContact._meta.local_fields if i.name not in exclude]
    sf_key = [i.name for i in sfcontact._meta.local_fields if i.name not in exclude]
    [i.sort(key=lambda x: x.lower()) for i in [rep_key,sf_key ]]

    rep_headers= request.session['repCSV_headers']
    sf_headers= request.session['sfCSV_headers']

    rep_dropdown = {i: sorted(rep_headers, key= lambda x: SeqMat(None, x, i).ratio(), reverse=True) for i in rep_key}
    sf_dropdown = {i: sorted(sf_headers, key= lambda x: SeqMat(None, x, i).ratio(), reverse=True) for i in sf_key}
    # print(json.dumps(rep_dropdown, indent=4))
    # print(json.dumps(sf_dropdown, indent=4))

    return render(request, 'dedupper/field_mapping.html', {'rep_dropdown': rep_dropdown,
                                                           'sf_dropdown': sf_dropdown
                                                           }
                  )

def merge(request, id):
    obj = repContact.objects.values().get(id=id)
    ids = [obj['closest1_contactID'], obj['closest2_contactID'], obj['closest3_contactID']]
    objs = sfcontact.objects.values().filter(ContactID__in=ids)
    fields = [i.name for i in repContact._meta.local_fields]
    mergers = list()

    for i in range(len(objs)):
        if objs[i]['ContactID'] == obj['closest1_contactID']:
            del objs[i]['closest_rep_id'], objs[i]['dupFlag'], objs[i]['ContactID']
            mergers.insert(0, list(objs[i].values()))
        elif objs[i]['ContactID'] == obj['closest2_contactID']:
            del objs[i]['closest_rep_id'], objs[i]['dupFlag'], objs[i]['ContactID']
            mergers.insert(len(mergers), list(objs[i].values()))
        else:
            del objs[i]['closest_rep_id'], objs[i]['dupFlag'], objs[i]['ContactID']
            mergers.insert(-1, list(objs[i].values()))

    del obj['closest1_id'], obj['closest2_id'], obj['closest3_id'], obj['closest1_contactID'], \
        obj['closest2_contactID'], obj['closest3_contactID'], obj['type'], obj['dupFlag'], obj['average']
    obj = list(obj.values())
    if len(mergers) == 3:
        obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0],mergers[1],mergers[2])) ) }
    elif len(mergers) == 2:
        obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0],mergers[1])) ) }
    elif len(mergers) == 1:
        obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0])) ) }
    return render(request, 'dedupper/merge.html', {'objs' : obj_map})

def progress(request):
    if request.method == 'GET':
        reps = len(repContact.objects.all())
        dups = len(repContact.objects.filter(type='Duplicate'))
        news = len(repContact.objects.filter(type='New Record'))
        undies = len(repContact.objects.filter(type='Undecided'))
        manu = len(repContact.objects.filter(type='Manual Check'))
        doneKeys, numKeys, currKey, doneReps = get_progress()
        keyPercent = round(((doneKeys/numKeys)*100) + ((1/numKeys) * (doneReps/reps)*100),2)
        repPercent = round(100*(reps-undies)/reps,2)
        key_stats = []
        for i in keys:
            key = '-'.join(i)
            title = ' '.join(i)
            undies = len(repContact.objects.filter(type='Undecided', keySortedBy=key))
            dups = len(repContact.objects.filter(type='Duplicate', keySortedBy=key))
            news = len(repContact.objects.filter(type='New Record', keySortedBy=key))
            manu = len(repContact.objects.filter(type='Manual Check', keySortedBy=key))
            key_stats.append({'title': title, 'undies': undies, 'dups': dups, 'news': news, 'manu': manu})
        stats_table = StatsTable(key_stats)

    return JsonResponse({'reps': reps, 'dups': dups, 'news': news, 'undies':undies, 'doneKeys': doneKeys,
                         'numKeys': numKeys, 'doneReps': doneReps, 'currKey':currKey, 'manu': manu,
                         'keyPercent': keyPercent, 'repPercent': repPercent, 'table': stats_table.as_html(request)},
                        safe=False)

def resort(request):
    if request.method == 'GET':
        print('resorting')
        set_sorting_algorithm(int(request.GET.get('upper_thres')), int(request.GET.get('lower_thres')))
    return JsonResponse({'msg': 'success!'}, safe=False)

def run(request):
    global keys
    if request.method == 'GET':
        keylist = request.GET.get('keys')
        #channel = request.GET.get('channel')
        keylist = keylist.split("_")
        partslist = [i.split('-') for i in keylist[:-1]]
        keys=partslist
        result = key_generator(partslist)
    return JsonResponse({'msg': 'success!'}, safe=False)

def upload(request):
    global export_headers, keys

    print('uploading file')
    form = UploadFileForm(request.POST, request.FILES)
    repCSV = request.FILES['repFile']
    sfCSV = request.FILES['sfFile']
    rep_headers, pd_rep_csv = convert_csv(repCSV)
    request.session['repCSV_headers'] = rep_headers
    export_headers = rep_headers

    sf_headers, pd_sf_csv= convert_csv(sfCSV)
    request.session['sfCSV_headers'] = sf_headers
    # keys = make_keys(headers)
    with open(settings.REP_CSV, 'wb') as file:
        pickle.dump(pd_rep_csv, file)
        print('pickle dump reps')

    with open(settings.SF_CSV, 'wb') as file:
        pickle.dump(pd_sf_csv, file)
        print('pickle dump sf')

    return redirect('/map/')

