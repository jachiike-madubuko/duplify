from django.db import models
import json
from django.utils import timezone

# Create your models here.
class FinraContact(models.Model):
    crd = models.CharField(max_length=100, null=True)
    data = models.TextField()
    date = models.DateTimeField(default=timezone.now)

    @property
    def to_dict(self):
        data = {
            'data' : json.loads(self.data),
            'date' : self.date,
        }
        return data

    def __str__(self):
        return self.crd
