"""
Change your models (in models.py).
Run python django423/mysite/manage.py makemigrations to create migrations for those changes
Run python django423/mysite/manage.py migrate --run-syncdb to apply those changes to the database.
"""

from __future__ import unicode_literals

from django.db import models

class Simple(models.Model):
    title = models.CharField(max_length=128)
    author = models.CharField(max_length=128)
    category = models.CharField(max_length=128)

    def __unicode__(self):
        return '{} by {} ({})'.format(self.title, self.author, self.category)