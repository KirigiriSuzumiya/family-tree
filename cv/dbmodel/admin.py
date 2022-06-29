from django.contrib import admin

from .models import People, FaceImage, Image


class PeopleAdmin(admin.ModelAdmin):
    # ...
    list_display = ('name', 'id', 'visited', 'visit_time')
    search_fields = ('id', 'name')


class FaceImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'upload_time')


# Register your models here.
admin.site.register(People, PeopleAdmin)
admin.site.register(FaceImage, FaceImageAdmin)
admin.site.register(Image)
admin.site.site_header = '人脸数据后台管理系统'
