import csv
import datetime
import json
import pickle
from difflib import SequenceMatcher as SeqMat
from io import BytesIO

import tablib
from django.core.management import call_command
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django_tables2.views import RequestConfig

from dedupper.forms import UploadFileForm
from dedupper.tables import StatsTable, SFContactTable, RepContactTable
from dedupper.utils import *

tablib.formats.json.json = json
keys= []
name_sort=address_sort=email_sort=crd_sort=phone_sort=average_sort=key_sort=True

def display(request):
    return render(request, 'dedupper/data-table.html')

def closest(request):
    #function gets the SFContactTable for each of the closest matches
    if request.method == 'GET':
        id = request.GET.get('id')
        close_id1 = request.GET.get('close1')
        close_id2 = request.GET.get('close2')
        close_id3 = request.GET.get('close3')
        html_table1=html_table2=html_table3=''

        #check if id exists, if so: render html table of the contact
        if close_id1 != '':
            table1 = SFContactTable( sfcontact.objects.filter(pk=close_id1))
            html_table1 = table1.as_html(request)
        if close_id2 != '':
            table2 = SFContactTable( sfcontact.objects.filter(pk=close_id2))
            html_table2 = table2.as_html(request)
        if close_id3 != '':
            table3 = SFContactTable( sfcontact.objects.filter(pk=close_id3))
            html_table3 = table3.as_html(request)

        return JsonResponse({ 'table1': html_table1, 'table2':html_table2, 'table3': html_table3}, safe=False)
        # return  JsonResponse({'rep-table': 'tits'})

def turn_table(request):
    #function that returns a table of contact types sorted by a user input field
    if request.method == 'GET':
        type =  request.GET.get('type')
        sort =  request.GET.get('sorting')
        #switch statement on sort field
        if sort =='name':
            #booleans for each sorting field to toggle between ascending and descending
            if globals()['name_sort']:
                globals()['name_sort'] = False
                table = RepContactTable(repContact.objects.filter(type=type).order_by('lastName', 'firstName'))
            else:
                globals()['name_sort'] = True
                table = RepContactTable(repContact.objects.filter(type=type).order_by('-lastName', '-firstName'))
        elif sort =='email':
            if globals()['email_sort']:
                globals()['email_sort'] = False
                table = RepContactTable(repContact.objects.filter(type=type).order_by('workEmail'))
            else:
                globals()['name_sort'] = True
                table = RepContactTable(repContact.objects.filter(type=type).order_by('-workEmail'))
        elif sort =='phone':
            if globals()['name_sort']:
                globals()['name_sort'] = False
                table = RepContactTable(repContact.objects.filter(type=type).order_by('Phone'))
            else:
                globals()['name_sort'] = True
                table = RepContactTable(repContact.objects.filter(type=type).order_by('-Phone'))
        elif sort =='address':
            if globals()['name_sort']:
                globals()['name_sort'] = False
                table = RepContactTable(repContact.objects.filter(type=type).order_by('mailingStateProvince', 'mailingCity'))
            else:
                globals()['name_sort'] = True
                table = RepContactTable(repContact.objects.filter(type=type).order_by('-mailingStateProvince', '-mailingCity'))
        elif sort =='average':
            if globals()['name_sort']:
                globals()['name_sort'] = False
                table = RepContactTable(repContact.objects.filter(type=type).order_by('average'))
            else:
                globals()['name_sort'] = True
                table = RepContactTable(repContact.objects.filter(type=type).order_by('-average'))
        elif sort =='keySortedBy':
            if globals()['name_sort']:
                globals()['name_sort'] = False
                table = RepContactTable(repContact.objects.filter(type=type).order_by('keySortedBy'))
            else:
                globals()['name_sort'] = True
                table = RepContactTable(repContact.objects.filter(type=type).order_by('-keySortedBy'))
        elif sort =='CRD':
            if globals()['crd_sort']:
                globals()['crd_sort'] = False
                table = RepContactTable(repContact.objects.filter(type=type).order_by('CRD'))
            else:
                globals()['crd_sort'] = True
                table = RepContactTable(repContact.objects.filter(type=type).order_by('-CRD'))
        else:
            table = RepContactTable(repContact.objects.filter(type=type))
        config = RequestConfig(request, paginate={'per_page': 250})
        config.configure(table)
        print('sending table')
        return JsonResponse({ 'table': table.as_html(request) }, safe=False)


def download(request,type):
    output = BytesIO()
    writer = pd.ExcelWriter(output)

    #csv headers
    fields = ('id','CRD', 'First', 'Last', 'Street', 'City',
              'State', 'Zip', 'Phone', 'Home Phone', 'Mobile Phone',
              'Other Phone', 'Work Email', 'Personal Email', 'Other Email', 'Match Score', 'Key' )

    #flag to remove contactIDs from new records
    no_id = None

    #name of uploaded rep list
    if 'repCSV_name' in request.session:
        repCSV_name = request.session['repCSV_name'].replace('.csv','').replace('.xlsx','')
    #name the csv
    if(type == "Duplicate"):
        filename = f'filename="{repCSV_name} (Duplicates).csv"'
    elif(type == "NewRecord"):
        filename = f'filename= "{repCSV_name} (New Records).csv"'
        type = 'New Record'
        no_id = '.'
    elif(type == "ManualCheck"):
        filename = f'filename="{repCSV_name} (Manual Checks).csv"'
        type = 'Manual Check'
    else:
        filename = f'filename="{repCSV_name} (Undecided Records).csv"'


    for type in ['New Record', 'Duplicate' ]:
        rep_resource = RepContactResource()
        users = repContact.objects.filter(type = type)
        dataset = rep_resource.export(users)
        db_df = pd.read_json(dataset.json)

        #parse the misc field  back into their respective fields
        misc_df = db_df['misc'].astype(str).str.split('-!-', expand=True)
        db_df=db_df.drop('misc', axis=1)

        f = list(db_df[['average', 'keySortedBy', 'closest1_contactID']])
        with open(settings.REP_CSV, 'rb') as file:
            pd_rep_csv = pickle.load(file)
            print('pickle load reps')
        fields =  f + list(pd_rep_csv)
        fields[fields.index('closest1_contactID')] = 'ContactID'

        frames=[db_df[['average', 'keySortedBy', 'closest1_contactID']], misc_df]
        export = pd.concat(frames, axis=1)
        export.columns = fields
        if 'New' in type:
            del export['ContactID']
            fields.remove('ContactID')
        export.replace('nan', '', inplace=True)
        export.to_excel(writer, sheet_name=f'{type}', index=False)

    writer.save()
    writer.close()

    output.seek(0)

    #create response
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml'
                                                     '.sheet')
    filename = f'filename="{repCSV_name} (Duplified).xlsx"'
    response['Content-Disposition'] = 'attachment; '+filename

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
    elif(type == "A"):
        if 'repCSV_name' in request.session:
            repCSV_name = request.session['repCSV_name']
        else:
            repCSV_name = 'a Rep list'

        if 'sfCSV_name' in request.session:
            sfCSV_name = request.session['sfCSV_name']
        else:
            sfCSV_name = 'a Salesforce Channel'
        total_reps = repContact.objects.all().count()
        total_sf = sfcontact.objects.all().count()
        total_dups = repContact.objects.filter(type='Duplicate').count()
        percent_dups = round((total_dups/total_reps)*100,1)
        total_news = repContact.objects.filter(type='New Record').count()
        percent_news = round((total_news/total_reps)*100,1)
        time_hours = datetime.timedelta(seconds=duplifyTime.objects.get(pk=1).seconds)
        audit_info = []
        audit_info.append([f"Duplify Audit of {repCSV_name} duped against {sfCSV_name}"])
        audit_info.append([""])
        audit_info.append([f"Number of Records in Rep List: {total_reps} \t Number of Records in th{sfCSV_name[2:]}: " +
                          f"{total_sf}"])

        audit_info.append([f"Number of Duplicates in the Rep List: {total_dups}({percent_dups}%)"])
        audit_info.append([f"Number of News in the Rep List: {total_news}({percent_news}%)"])
        audit_info.append([f"Time: {time_hours}"])
        audit_info.append([""])
        audit_info.append(["Thank you for using Duplify!"])

        filename = 'filename="Audit.txt"'
        response = HttpResponse(content_type='text/text')
        response['Content-Disposition'] = 'attachment; ' + filename
        writer = csv.writer(response, delimiter='\n')
        writer.writerows(audit_info)
        return response
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
    return redirect('/map')

def import_csv(request):
    if request.method == 'GET':                 #expect getJSON request
        channel = request.GET.get('channel')    #sf channel to pull from db
        rep_header_map = request.GET.get('rep_map') #the JSON of csv headers mapped to db fields
        rep_header_map = json.loads(rep_header_map) #JSON -> dict()

        request.session['sfCSV_name'] = f'the {channel} channel'        #for printing

        db_data = {                         #packing data
            'channel': channel,
            'map' : rep_header_map
        }
        #the csv headers are stored to be used for exporting
        #get_channel queries the channel and loads the rep list and sf contacts
        request.session['misc'] =list   ( rep_header_map.keys())
        get_channel( db_data)

    return JsonResponse({'msg': 'success!'}, safe=False)

def index(request):
    return render(request, 'dedupper/login.html')

def upload_page(request):
    return render(request, 'dedupper/rep_list_upload.html')

def key_gen(request):
    try:
        if  'key_n_stats' in request.session:
            key =  request.session['key_n_stats']
        else:
            key = make_keys([i.name for i in repContact._meta.local_fields])
            request.session['key_n_stats'] = key
    except:
        key = [('error', 100, 0, 100, 0, 100)]
    return render(request, 'dedupper/key_generator.html', {'keys': key})

def login(request):
    u = request.GET.get('username')
    p = request.GET.get('password')
    try:
        sf = Salesforce(password=p,
                        username=u, security_token='W4ItPbGFZHssUcJBCZlw2t9p2')
        msg= 'success'
        #store u & p in session, create function called login_check that makes sure a username is in the session
        # else, redirect to /
    except:
        msg = 'failure'

    return JsonResponse({'msg': msg}, safe=False)

def map(request):
    return render(request, 'dedupper/field_mapping.html',
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

    del obj['closest1_id'], obj['closest2_id'], obj['closest3_id'], obj['closest1_contactID'], obj['closest2_contactID'], obj['closest3_contactID'], obj['type'], obj['dupFlag'], obj['average']
    obj = list(obj.values())
    if len(mergers) == 3:
        obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0],mergers[1],mergers[2])) ) }
    elif len(mergers) == 2:
        obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0],mergers[1])) ) }
    elif len(mergers) == 1:
        obj_map = {i:j for i,j in zip(fields, list(zip(obj,mergers[0])) ) }
    return render(request, 'dedupper/sort_view.html', {'objs' : obj_map})

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

def db_progress(request):
    if request.method == 'GET':
      if db_done():
          msg = 'success'
      else:
          msg = 'not yet'
          print(msg)

    return JsonResponse({
        'msg': msg
    }, safe=False)

def resort(request):
    if request.method == 'GET':
        print('resorting')
        set_sorting_algorithm(int(request.GET.get('upper_thres')), int(request.GET.get('lower_thres')))
    return JsonResponse({'msg': 'success!'}, safe=False)

def contact_sort(request):
    if request.method == 'GET':
        data = request.GET.getlist("data[]")
        rep = repContact.objects.get(pk=data[1])
        if data[0] == 'Duplicate':
            print(f"old order: {rep.closest1}, {rep.closest2}, {rep.closest3}")
            rep.type = 'Duplicate'
            if rep.closest3 and int(data[2]) == rep.closest3.id:
                print('moving 3rd closest to 1st')
                rep.closest1, rep.closest2, rep.closest3 =  rep.closest3, rep.closest1, rep.closest2
                rep.closest1_contactID, rep.closest2_contactID, rep.closest3_contactID =  rep.closest3_contactID, rep.closest1_contactID, rep.closest2_contactID
            elif rep.closest2 and int(data[2]) == rep.closest2.id:
                print('moving 2nd closest to 1st')
                rep.closest1, rep.closest2 = rep.closest2, rep.closest1
                rep.closest1_contactID, rep.closest2_contactID =rep.closest2_contactID,  rep.closest1_contactID
            print(f"new order: {rep.closest1}, {rep.closest2}, {rep.closest3}")
        elif data[0] == 'New Record':
            rep.type = 'New Record'
            rep.closest1_contactID = ''
        rep.save()
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
    request.session['repCSV_name'] = str(repCSV)
    rep_headers, pd_rep_csv = convert_csv(repCSV)
    request.session['repCSV_headers'] = rep_headers
    export_headers = rep_headers

    # keys = make_keys(headers)
    with open(settings.REP_CSV, 'wb') as file:
        pickle.dump(pd_rep_csv, file)
        print('pickle dump reps')

    exclude = ('id', 'misc', 'average', 'type', 'closest1_contactID', 'closest1', 'closest2_contactID', 'closest2', 'closest3_contactID', 'closest3', 'dupFlag', 'keySortedBy', 'closest_rep')
    rep_key = [i.name for i in repContact._meta.local_fields if i.name not in exclude]
    [i.sort(key=lambda x: x.lower()) for i in [rep_key ]]

    rep_headers= request.session['repCSV_headers']
    rep_dropdown = {i: sorted(rep_headers, key= lambda x: SeqMat(None, x, i).ratio(), reverse=True) for i in rep_key}


    print(rep_dropdown)
    return JsonResponse( rep_dropdown, safe=False)

