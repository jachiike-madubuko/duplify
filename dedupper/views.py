from django.shortcuts import render
from django.views.generic import TemplateView, ListView
import django_tables2
from dedupper.models import DedupTime, DuplifyTime, UploadTime,  SFContact, RepContact
from  dedupper.filters import SimpleFilter
from dedupper.tables import SimpleTable, ContactTable, RepContactTable
from tablib import Dataset
from django.http import HttpResponse
from django.shortcuts import render, redirect
from dedupper.forms import UploadFileForm
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin, RequestConfig

from dedupper.resources import RepContactResource, SFContactResource, DedupTimeResource, DuplifyTimeResource, UploadTimeResource
from  dedupper.utils import key_generator, makeKeys, convertCSV
import csv
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

def index(request):
    return render(request, 'dedupper/rep_list_upload.html')

def run(request):
    if request.method == 'POST':
        # move into new method seperate displaying and form submission to get rid of do you want to resubmit form
        keylist = request.POST.get('keys')
        print(keylist)
        # read in channel and query SF by channgel for the key gen
        # keylist = request.POST.get('channel')
        keylist = keylist.split("_")
        partslist = [i.split('-') for i in keylist[:-1]]
        key_generator(partslist)
    return redirect('/sorted-reps/')

#connect this page with filters config = RequestConfig(request)
def display(request):

    config = RequestConfig(request)
    undecided_table = RepContactTable(RepContact.objects.filter(type__exact='Undecided'), prefix='U-')  # prefix specified
    duplicate_table = RepContactTable(RepContact.objects.filter(type__exact='Duplicate'), prefix='D-')  # prefix specified
    new_record_table = RepContactTable(RepContact.objects.filter(type__exact='New Record'), prefix='N-')  # prefix
    # specified
    config.configure(undecided_table)
    config.configure(duplicate_table)
    config.configure(new_record_table)

    undecided = RepContactResource().export(RepContact.objects.filter(type='Undecided'))
    newRecord = RepContactResource().export(RepContact.objects.filter(type='New Record'))
    duplicate = RepContactResource().export(RepContact.objects.filter(type='Duplicate'))

    return render(request, 'dedupper/sorted.html', {
        'undecided_table': undecided_table,
        'duplicate_table': duplicate_table,
        'new_record_table': new_record_table,
    })

def upload(request):
    global export_headers, keys
    repcontact_resource = RepContactResource()
    sfcontact_resource = SFContactResource()
    dataset = Dataset()

    print('uploading file')
    form = UploadFileForm(request.POST, request.FILES)
    repCSV = request.FILES['repFile']
    sfCSV = request.FILES['sfFile']
    print('reps')
    headers = convertCSV(repCSV, repcontact_resource, batchSize=100)
    export_headers = headers
    print(headers)
    print('SF')
    convertCSV(sfCSV, sfcontact_resource, type='SF', batchSize=100)

    keys = makeKeys(headers)

    return redirect('/key-gen/', {'keys': keys})

def merge(request, CRD):
    obj = RepContact.objects.values().get(CRD=CRD)
    ids = [obj['closest1_id'], obj['closest2_id'], obj['closest3_id']]
    objs = SFContact.objects.values().filter(pk__in=ids)
    fields = [i.name for i in RepContact._meta.local_fields]
    mergers = list()

    for i in range(len(objs)):
        del objs[i]['closest1_id'], objs[i]['closest2_id'], objs[i]['closest3_id'], objs[i]['type'], objs[i]['average'],
        mergers.append(list(objs[i].values()))
    del obj['closest1_id'], obj['closest2_id'], obj['closest3_id'], obj['type'], obj['average']
    obj = list(obj.values())


    if len(mergers) == 3:
        obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0],mergers[1],mergers[2])) ) }
    elif len(mergers) == 2:
        obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0],mergers[1])) ) }
    elif len(mergers) == 1:
        obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0])) ) }
    print(obj_map)
    '''
        outputs a dictionary of the field as the with a value of each objs corresponding field value
        example
        obj_map['title'] = ('free willy', 'home alone', 'toy story')
    '''
    return render(request, 'dedupper/merge.html', {'objs' : obj_map})

def download(request,type):
    export_headers = list(list(RepContact.objects.all().values())[0].keys())

    if(type == "Duplicate"):
        filename = 'filename="Duplicates.csv"'
    elif(type == "NewRecord"):
        filename = 'filename="New Records.csv"'
        type = 'New Record'
    else:
        filename = 'filename="Undecided Records.csv"'

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; '+filename

    writer = csv.writer(response)
    writer.writerow(export_headers)

    users = RepContact.objects.filter(type = type).values_list(*export_headers)
    for user in users:
        writer.writerow(user)

    return response

def download_times(request,type):
    if(type == "DD"):
        filename = 'filename="Dedup Times.csv"'
        times = DedupTime.objects.all().values_list()
        export_headers = [i.name for i in DedupTime._meta.local_concrete_fields]
    elif(type == "D"):
        filename = 'filename="Duplify Times.csv"'
        times = DuplifyTime.objects.all().values_list()
        export_headers = [i.name for i in DuplifyTime._meta.local_concrete_fields]
    else:
        filename = 'filename="Upload Times.csv"'
        times = UploadTime.objects.all().values_list()
        export_headers = [i.name for i in UploadTime._meta.local_concrete_fields]


    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; '+filename
    writer = csv.writer(response)
    writer.writerow(export_headers)

    for time in times:
        writer.writerow(time)

    return response

def key_gen(request):
    key = makeKeys([i.name for i in RepContact._meta.local_concrete_fields])
    return render(request, 'dedupper/key_generator.html', {'keys': key})
