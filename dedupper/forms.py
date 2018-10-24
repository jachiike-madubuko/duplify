from django import forms

from dedupper.models import *


class UploadFileForm(forms.Form):
    file = forms.FileField()


class IndudstryForm(forms.ModelForm):
    class Meta():
        model = industry
        fields = ['title', 'link', 'description', 'archived']
