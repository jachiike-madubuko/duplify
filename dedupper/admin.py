from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(industry)
admin.site.register(manufacturer)
admin.site.register(sfcontact)
admin.site.register(repContact)
admin.site.register(dedupTime)
admin.site.register(duplifyTime)
admin.site.register(uploadTime)
