from django.shortcuts import render
from django.views.generic import TemplateView, ListView
import django_tables2
from dedupper.models import Simple
from  dedupper.filters import SimpleFilter
from dedupper.tables import SimpleTable
from tablib import Dataset
from django.http import HttpResponse
from django.shortcuts import render
from dedupper.forms import UploadFileForm
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin, RequestConfig

from dedupper.resources import SimpleResource
from  dedupper.utils import key_generator
import csv

#TODO create views for the different tables

#TODO add interface for views closest match records

#TODO Create document merging interface

#TODO Interactive Table

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
        keylist = request.POST.get('keys')
        keylist = keylist.split("_")
        partslist = [i.split('-') for i in keylist[:-1]]
        key_generator(partslist)

    config = RequestConfig(request)
    undecided_table = SimpleTable(Simple.objects.filter(type__exact='Undecided'), prefix='U-')  # prefix specified
    duplicate_table = SimpleTable(Simple.objects.filter(type__exact='Duplicate'), prefix='D-')  # prefix specified
    new_record_table = SimpleTable(Simple.objects.filter(type__exact='New Record'), prefix='N-')  # prefix specified
    config.configure(undecided_table)
    config.configure(duplicate_table)
    config.configure(new_record_table)

    return render(request, 'dedupper/sorted.html', {
        'undecided_table': undecided_table,
        'duplicate_table': duplicate_table,
        'new_record_table': new_record_table,
    })


def upload(request):
    simple_resource = SimpleResource()
    dataset = Dataset()
    new_simples = list()

    print('uploading file')
    form = UploadFileForm(request.POST, request.FILES)
    if 'myfile' in request.session:
        uploadedfile = request.session['myfile']
    else:
        uploadedfile = request.FILES['myfile']


    fileString = ''
    for chunk in uploadedfile.chunks():
        fileString += chunk.decode("utf-8") + '\n'
    print('done decoding')
    print('load data')
    dataset.csv = fileString
    print('done data load')

    result = simple_resource.import_data(dataset, dry_run=True)  # Test the data import
    if not result.has_errors():
        print('importing data')
        simple_resource.import_data(dataset, dry_run=False)  # Actually import now
    return render(request, 'dedupper/key_generator.html', {'headers': dataset.headers})


def merge(request, title):
    obj = Simple.objects.values().get(title=title)
    ids = [obj['closest1_id'], obj['closest2_id'], obj['closest3_id']]
    objs = Simple.objects.values().filter(pk__in=ids)
    fields = [i.name for i in Simple._meta.local_fields][:-3]
    mergers = list()

    for i in range(len(objs)):
        del objs[i]['closest1_id'], objs[i]['closest2_id'], objs[i]['closest3_id'], objs[i]['type'], objs[i]['average'],
        mergers.append(list(objs[i].values()))
    del obj['closest1_id'], obj['closest2_id'], obj['closest3_id'], obj['type'], obj['average']
    obj = list(obj.values())

    obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0],mergers[1],mergers[2])) ) }
    print(obj_map)
    '''
        outputs a dictionary of the field as the with a value of each objs corresponding field value
        example
        obj_map['title'] = ('free willy', 'home alone', 'toy story')
    '''
    x = [ i for i in range(50)]
    return render(request, 'dedupper/merge.html', {'objs' : obj_map, 'cnt':x})

