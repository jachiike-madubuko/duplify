from import_export import resources
from .models import simple, repContact, sfcontact, duplifyTime, dedupTime, uploadTime
from import_export.fields import Field


class DuplifyTimeResource(resources.ModelResource):
    class Meta:
        model = duplifyTime
        
class DedupTimeResource(resources.ModelResource):
    class Meta:
        model = dedupTime

class UploadTimeResource(resources.ModelResource):
    class Meta:
        model = uploadTime

class RepContactResource(resources.ModelResource):

    class Meta:
        model = repContact
        exclude = ('closest1','closest2','closest3','average','type','dupFlag')

class SFContactResource(resources.ModelResource):
    class Meta:
        model = sfcontact


