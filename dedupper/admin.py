from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from dedupper.resources import *

# Register your models here.
admin.site.register(sfcontact)
admin.site.register(repContact)


class SFContactAdmin(ImportExportModelAdmin):
    resource_class = SFContactResource


class RepContactAdmin(ImportExportModelAdmin):
    resource_class = RepContactResource
