from django.contrib import admin
from .models import Simple, Contact, SFContact, RepContact, DedupTime, DuplifyTime, UploadTime

# Register your models here.
admin.site.register(SFContact)
admin.site.register(RepContact)
admin.site.register(DedupTime)
admin.site.register(DuplifyTime)
admin.site.register(UploadTime)
