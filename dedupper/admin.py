from django.contrib import admin
from .models import simple, sfcontact, repContact, dedupTime, duplifyTime, uploadTime

# Register your models here.
admin.site.register(sfcontact)
admin.site.register(repContact)
admin.site.register(dedupTime)
admin.site.register(duplifyTime)
admin.site.register(uploadTime)
