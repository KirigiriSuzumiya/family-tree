from django.db import models
from django.utils import timezone
import requests
import os
import json
from cv.settings import BASE_DIR
# Create your models here.
config_path = os.path.join(os.path.dirname(__file__),"..","..","config.json")
auth_config = json.load(open(config_path,"r"))
api_key = auth_config["face_api_key"]
secret_key = auth_config["face_secret_key"]

class People(models.Model):
    name = models.CharField(max_length=100, default='')
    first_name = models.CharField(max_length=50, blank=True, null=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    sex_choice = models.TextChoices('male', 'female')
    sex = models.CharField(blank=True, choices=sex_choice.choices, max_length=20, null=True)
    birth_date = models.DateTimeField(blank=True, null=True)
    death_date = models.DateTimeField(blank=True, null=True)
    xing = models.CharField(max_length=100, blank=True, null=True)
    ming = models.CharField(max_length=100, blank=True, null=True)
    zi = models.CharField(max_length=100, blank=True, null=True)
    other_name = models.CharField(max_length=100, blank=True, null=True)


    mate = models.CharField(max_length=50, blank=True, null=True)
    father = models.CharField(max_length=50, blank=True, null=True)
    mother = models.CharField(max_length=50, blank=True, null=True)
    kids = models.JSONField(blank=True, null=True)
    info = models.CharField(max_length=50000, blank=True, null=True)
    family_name = models.CharField(max_length=100, blank=True, null=True)

    visited = models.IntegerField(default=0)
    visit_time = models.CharField(max_length=50000, blank=True, null=True)
    institute = models.CharField(max_length=50000, blank=True, null=True)
    edu = models.CharField(max_length=50000, blank=True, null=True)
    located_time = models.CharField(max_length=50000, blank=True, null=True)

    def __str__(self):
        return self.name

class Image(models.Model):
    path = models.CharField(max_length=1000)
    token_time = models.DateTimeField(blank=True, null=True)
    info = models.CharField(max_length=50000, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    count = models.IntegerField(blank=True, null=True)
    use_baidu = models.BooleanField(default=False)
    loc_x = models.CharField(max_length=50, blank=True, null=True)
    loc_y = models.CharField(max_length=50, blank=True, null=True)
    loc_info = models.CharField(max_length=50, blank=True, null=True)
    def __str__(self):
        return self.path


class FaceImage(models.Model):
    path = models.CharField(max_length=50000, primary_key=True)
    upload_time = models.DateTimeField(default=timezone.now)
    name = models.ForeignKey(People, on_delete=models.CASCADE, null=True)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    token = models.CharField(max_length=50000, null=True, blank=True)
    logid = models.CharField(max_length=50000, null=True, blank=True)
    def __str__(self):
        return self.path
    def delete(self):
        # 重载faceimage delete方法，在删除数据库前删除baidu api的人脸库
        try:
            host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (api_key, secret_key)
            response = requests.get(host)
            if response:
                access_token = response.json()["access_token"]
            else:
                raise "get access token failed"
            # 设置请求包体
            request_url = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/face/delete"
            request_url = request_url + "?access_token=" + access_token
            headers = {'content-type': 'application/json'}
            path = self.path
            params = '{"log_id":%s,"group_id":"admin","user_id":"%d","face_token":"%s"}' % (self.logid, self.name.id, self.token)
            response = requests.post(request_url, data=params, headers=headers)
            print(response.json())
            img_path = os.path.join(BASE_DIR, 'cv', 'model_image')
            os.remove(os.path.join(img_path, path))
        except Exception as e:
            print(e)
        return super().delete()


class Location(models.Model):
    belongs_to = models.ForeignKey(People, on_delete=models.CASCADE)
    loc_x = models.CharField(max_length=50, blank=True, null=True)
    loc_y = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    description = models.CharField(max_length=5000, blank=True, null=True)
