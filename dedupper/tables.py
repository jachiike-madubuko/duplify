import django_tables2 as tables
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
        attrs = {'class' : 'table table-hover table-striped table-dark' }

class ContactTable(tables.Table):
    merge = tables.LinkColumn('merge_records', args=[tables.A('pk')], attrs={'class': 'btn btn-outline-primary', 'href':"#" }, text="Merge")
    def render_merge(self, record):
        href = record.id
        return mark_safe('<a id="yo" class="btn btn-outline-primary" onclick="merge()" href="'+str(href)+'" Merge>Merge</a>')

    class Meta:
        model = contact
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class' : 'table table-hover table-striped table-dark' }

class RepContactTable(tables.Table):
    merge = tables.LinkColumn('merge_records', args=[tables.A('pk')], attrs={'class': 'btn btn-outline-primary badge-pill',
                                                                             'href':"#" }, text="Merge")

    def render_merge(self, record):
        href = record.CRD
        return mark_safe('<a id="yo" class="btn btn-outline-primary" onclick="merge()" href="'+str(href)+'" Merge>Merge</a>')

    class Meta:
        model = repContact
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class' : 'table table-hover table-striped table-dark' }
        sequence = ('closest1', 'closest1_contactID', 'closest2', 'closest2_contactID', 'closest3', 'closest3_contactID', 'merge',
                    'average', '...')
        exclude = ('cansellDate', 'levelGroup', 'regionalLeader', 'boaName', 'fieldTrainerLeader',
                   'id', 'canSellDate', 'performanceLeader', 'levelLeader', 'otherEmail', 'workEmail',
                   'personalEmail', 'otherPhone', 'Phone', 'dupFlag', 'type')


class SFContactTable(tables.Table):
    merge = tables.LinkColumn('merge_records', args=[tables.A('pk')], attrs={'class': 'btn btn-outline-primary badge-pill',
                                                                             'href':"#" }, text="Merge")

    def render_merge(self, record):
        href = record.CRD
        return mark_safe('<a id="yo" class="btn btn-outline-primary" onclick="merge()" href="'+str(href)+'" Merge>Merge</a>')

    class Meta:
        model = sfcontact
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class' : 'table table-hover table-striped table-dark' }

