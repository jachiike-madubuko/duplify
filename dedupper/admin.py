from django.contrib import admin
from .models import Simple, Contact, SFContact, RepContact

# Register your models here.
admin.site.register(Simple)
admin.site.register(Contact)
admin.site.register(SFContact)
admin.site.register(RepContact)
