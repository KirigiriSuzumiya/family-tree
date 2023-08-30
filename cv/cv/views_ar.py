import base64

import requests
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
import os
import time
from pathlib import Path
from .codes import FaceRecognition, FaceExtractor
from .settings import BASE_DIR
from dbmodel.models import FaceImage, People
from dbmodel.models import Image as image_db
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages
import subprocess
from pypinyin import lazy_pinyin
from django.core.paginator import Paginator
import re

# -*- coding: CP936 -*-

def ar(request):
    return render(request, 'device_control.html')
