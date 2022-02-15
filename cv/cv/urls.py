"""cv URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,re_path
from . import views
urlpatterns = [
    path(r'', views.index),
    path(r'index', views.index),
    path('about',views.about),
    path(r'admin/', admin.site.urls),
    path(r'faceupload', views.face_upload),
    path(r'pic_upload', views.pic_upload),
    path(r'name_upload', views.name_upload),
    path(r'recognition', views.recognition),
    path(r'recognition_upload', views.recognition_upload),
    path(r'namelist', views.namelist),
    re_path(r'facelist/(.*)$', views.facelist),
    re_path(r'face_edit/(.*)$', views.face_edit),
    re_path(r'edit_pic/(.*)$', views.edit_pic),
]




