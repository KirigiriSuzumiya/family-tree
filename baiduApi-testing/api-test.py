import sys
from io import BytesIO
from time import sleep
import time
import pandas as pd
import face_recognition
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
# from ..cv.cv.settings import BASE_DIR
import os
img_path = 'http://124.221.104.193/static/20220612193339.jpg'
# client_id 为官网获取的AK， client_secret 为官网获取的SK
# 获取access_token
api_key = "jkyuzoYl4Cly99sEmxNMZog3"
secret_key = "09UaoIt6Bu96g10Hjiyg2pnyW0QvRCrj"
host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (api_key, secret_key)
response = requests.get(host)
if response:
    access_token = response.json()["access_token"]
else:
    pass

# 设置请求包体
request_url = "https://aip.baidubce.com/rest/2.0/face/v3/detect"
request_url = request_url + "?access_token=" + access_token
headers = {'content-type': 'application/json'}
result = []
params = '{"image":"%s","image_type":"URL"}' % img_path
response = requests.post(request_url, data=params, headers=headers)
print(response.json())
if response.json()["error_msg"] != "SUCCESS":
    print("识别失败")
facelist = response.json()["result"]["face_list"]
for face in facelist:
    location = face["location"]
    print(location)
# 分割人脸并一一调用百度api
# for i in range(len(locations)):
#     result.append([])
#     box = (locations[i][3], locations[i][0], locations[i][1], locations[i][2])
#     face = origin.crop(box)
#     output_buffer = BytesIO()
#     pic_save_path = str(time.time())+img_path[img_path.rfind("."):]
#     pic_save_path = os.path.join(BASE_DIR, "statics", "temp_image", pic_save_path)
#     print(pic_save_path)
#     face.save(pic_save_path)
#     png = open(pic_save_path, 'rb')
#     res = png.read()
#     png.close()
#     image = base64.b64encode(res).decode("ascii")
#     params = '{"image":"%s","image_type":"BASE64","group_id_list":"admin","max_user_num":5,"match_threshold":60}' % image
#     response = requests.post(request_url, data=params, headers=headers)
#     print(response.json())
#     if response.json()["error_msg"] == "SUCCESS":
#         res_info = response.json()["result"]["face_list"][0]["user_list"]
#         for j in range(len(res_info)):
#             result[i].append({"id": res_info[j]["user_id"], "score": res_info[j]["score"]})
#     else:
#         result[i].append(response.json()["error_msg"])
#     sleep(0.5)
