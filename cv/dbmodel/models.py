from django.db import models
from django.utils import timezone
# Create your models here.


class People(models.Model):
    custom_id = models.IntegerField(default=0)
    name = models.CharField(max_length=100, default='', primary_key=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    mate = models.CharField(max_length=50, blank=True)
    father = models.CharField(max_length=50, blank=True)
    mother = models.CharField(max_length=50, blank=True)
    kids = models.JSONField(blank=True, null=True)
    info = models.CharField(max_length=500, blank=True)
    loc_x = models.CharField(max_length=50, blank=True)
    loc_y = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class FaceImage(models.Model):
    path = models.CharField(max_length=1000, primary_key=True)
    upload_time = models.DateTimeField(default=timezone.now)
    name = models.ForeignKey(People, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.path