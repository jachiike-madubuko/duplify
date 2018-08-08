import django_tables2 as tables
from django_tables2 import Column
from dedupper.models import simple, contact, repContact, sfcontact
from django_tables2.utils import AttributeDict
from django.utils.safestring import mark_safe

class SimpleTable(tables.Table):

    merge = tables.LinkColumn('merge_records', args=[tables.A('pk')], attrs={'class': 'btn btn-outline-primary', 'href':"#" }, text="Merge")

    def render_merge(self, record):
        href = record.title
        return mark_safe('<a id="yo" class="btn btn-outline-primary" onclick="merge()" href="'+str(href)+'" Merge>Merge</a>')

    class Meta:
        model = simple
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class' : 'table table-hover table-striped table-dark'}

class ContactTable(tables.Table):
    merge = tables.LinkColumn('merge_records', args=[tables.A('pk')], attrs={'class': 'btn btn-outline-primary', 'href':"#" }, text="Merge")
    def render_merge(self, record):
        href = record.id
        return mark_safe('<a id="yo" class="btn btn-outline-primary" onclick="merge()" href="'+str(href)+'" Merge>Merge</a>')

    class Meta:
        model = contact
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class' : 'table table-hover table-striped table-dark'}

class RepContactTable(tables.Table):
    sort = tables.LinkColumn('merge_records', args=[tables.A('pk')], attrs={'class': 'btn btn-outline-primary '
                                                                                    'badge-pill',
                                                                             'href': "#"}, text="Sort")
    name = Column(accessor='full_name', verbose_name='Name')
    email = Column(accessor='email', verbose_name='Email')
    phone = Column(accessor='phone', verbose_name='Phone')
    address = Column(accessor='locale', verbose_name='Location')


    def render_sort(self, record):
        href = str(record.id)
        href1 = ''
        href2 = ''
        href3 = ''
        if record.closest1:
            href1 = str(record.closest1.id)
        if record.closest2:
            href2 = str(record.closest2.id)
        if record.closest3:
            href3 = str(record.closest3.id)
        return mark_safe('<button type="button" class="btn btn-secondary" data-container="body" '
                         'data-toggle="popover" '
                         'data-placement="top" data-content="" data-id="'+href+'" data-id1="'+href1+'" data-id2="'
                         +href2+'" data-id3="' +href3+'">SORT</button>')
    class Meta:
        model = repContact
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class' : 'table table-hover table-striped table-dark table-sm' }
        fields = {'sort','average','CRD', 'name', 'email', 'phone', 'address', 'keySortedBy'}

        sequence = ('sort','average','keySortedBy','CRD', 'name', 'email', 'phone', 'address')
        exclude = ('cansellDate', 'levelGroup', 'regionalLeader', 'boaName', 'fieldTrainerLeader',
                   'id', 'canSellDate', 'performanceLeader', 'levelLeader', 'otherEmail', 'workEmail',
                   'personalEmail', 'otherPhone', 'Phone', 'dupFlag', 'type', 'closest1', 'closest1_contactID', 'closest2', 'closest2_contactID', 'closest3', 'closest3_contactID',)

class SFContactTable(tables.Table):
    link = tables.LinkColumn('link', args=[tables.A('pk')], attrs={'class': 'btn btn-outline-primary'}, text="Merge")
    name = Column(accessor='full_name', verbose_name='Name')
    email = Column(accessor='email', verbose_name='Email')
    phone = Column(accessor='phone', verbose_name='Phone')
    address = Column(accessor='locale', verbose_name='Location')

    def render_link(self, record):
        href = record.ContactID
        return mark_safe('<a class="btn btn-outline-primary" target="_blank" href="https://na30.salesforce.com/'+str(
            href)+'">View <span class="fa fa-external-link"></span></a>')

    class Meta:
        model = sfcontact
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class' : 'table table-hover table-sm'}
        fields = {'link','CRD', 'name', 'email', 'phone', 'address'}
        sequence = ('link','CRD', 'name', 'email', 'phone', 'address')

class StatsTable(tables.Table):
    title = Column()
    undies = Column()
    dups = Column()
    news = Column()
    manu = Column()

    class Meta:
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class': 'table table-hover table-striped table-sm bg-white'}