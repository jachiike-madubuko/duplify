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
    closest1_CRD = Field()
    closest2_CRD = Field()
    closest3_CRD = Field()

    class Meta:
        model = repContact

    def dehydrate_closest1_CRD(self, rep):
        if rep.closest1:
            return '{}'.format(rep.closest1.CRD)
        else:
            return ''

    def dehydrate_closest2_CRD(self, rep):
        if rep.closest2:
            return '{}'.format(rep.closest2.CRD)
        else:
            return ''

    def dehydrate_closest3_CRD(self, rep):
        if rep.closest3:
            return '{}'.format(rep.closest3.CRD)
        else:
            return ''

class SFContactResource(resources.ModelResource):
    class Meta:
        model = sfcontact


