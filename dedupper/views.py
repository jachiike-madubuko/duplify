from django.shortcuts import render
from django.views.generic import TemplateView, ListView
import django_tables2
from dedupper.models import Simple, Contact, RepContact
from  dedupper.filters import SimpleFilter
from dedupper.tables import SimpleTable, ContactTable, RepContactTable
from tablib import Dataset
from django.http import HttpResponse
from django.shortcuts import render
from dedupper.forms import UploadFileForm
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin, RequestConfig

from dedupper.resources import SimpleResource, ContactResource, RepContactResource, SFContactResource
from  dedupper.utils import key_generator, makeKeys, convertCSV
import csv

#TODO seperate url for form submission and for loading new pages use httpRedirect
#TODO method for saving



def index(request):
    return render(request, 'dedupper/rep_list_upload.html')


class FilteredSimpleListView(SingleTableMixin, FilterView):
    table_class = SimpleTable
    model = Simple
    template_name = 'simple_filter.html'

    filterset_class = SimpleFilter

#connect this page with filters config = RequestConfig(request)
def display(request):
    if request.method == 'POST':
        #move into new method seperate displaying and form submission to get rid of do you want to resubmit form
        keylist = request.POST.get('keys')
        print(keylist)
        #read in channel and query SF by channgel for the key gen
        #keylist = request.POST.get('channel')
        keylist = keylist.split("_")
        partslist = [i.split('-') for i in keylist[:-1]]
        key_generator(partslist)

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
    global export_headers
    repcontact_resource = RepContactResource()
    sfcontact_resource = SFContactResource()
    dataset = Dataset()

    print('uploading file')
    form = UploadFileForm(request.POST, request.FILES)
    repCSV = request.FILES['repFile']
    sfCSV = request.FILES['sfFile']

    headers = convertCSV(repCSV,repcontact_resource)
    export_headers = headers

    convertCSV(sfCSV,sfcontact_resource)

    keys = makeKeys(headers)

    return render(request, 'dedupper/key_generator.html', {'keys': keys})


def merge(request, CRD):
    obj = RepContact.objects.values().get(CRD=CRD)
    ids = [obj['closest1_id'], obj['closest2_id'], obj['closest3_id']]
    objs = RepContact.objects.values().filter(pk__in=ids)
    fields = [i.name for i in RepContact._meta.local_fields]
    mergers = list()

    for i in range(len(objs)):
        del objs[i]['closest1_id'], objs[i]['closest2_id'], objs[i]['closest3_id'], objs[i]['type'], objs[i]['average'],
        mergers.append(list(objs[i].values()))
    del obj['closest1_id'], obj['closest2_id'], obj['closest3_id'], obj['type'], obj['average']
    obj = list(obj.values())

    obj_map = {i:j for i,j in zip(fields, list(zip(obj,obj,obj,obj)) ) }
    #obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0],mergers[1],mergers[2])) ) }
    print(obj_map)
    '''
        outputs a dictionary of the field as the with a value of each objs corresponding field value
        example
        obj_map['title'] = ('free willy', 'home alone', 'toy story')
    '''
    x = [ i for i in range(50)]
    return render(request, 'dedupper/merge.html', {'objs' : obj_map, 'cnt':x})



def export(request,type):
    export_headers = list(list(RepContact.objects.all().values())[0].keys())

    if(type == "Duplicate"):
        filename = 'filename="Duplicates.xlsx"'
    elif(type == "New Record"):
        filename = 'filename="New Records.xlsx"'
    else:
        filename = 'filename="Undecided Records.xlsx"'

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; '+filename

    writer = csv.writer(response)
    writer.writerow(export_headers)

    users = RepContact.objects.filter(type = type).values_list(*export_headers)
    for user in users:
        writer.writerow(user)

    return response
#TODO add export functionality using django import export


