import sys
from io import BytesIO
from time import sleep
import time
import pandas as pd
import face_recognition
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
from ..cv.cv.settings import BASE_DIR
import os
img_path = 'image5.jpg'
# client_id 为官网获取的AK， client_secret 为官网获取的SK
# 获取access_token
api_key = "jkyuzoYl4Cly99sEmxNMZog3"
secret_key = "09UaoIt6Bu96g10Hjiyg2pnyW0QvRCrj"
host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (api_key, secret_key)
response = requests.get(host)
if response:
    access_token = response.json()["access_token"]
else:
    exit(0)

# 设置请求包体
request_url = "https://aip.baidubce.com/rest/2.0/face/v3/multi-search"
request_url = request_url + "?access_token=" + access_token
headers = {'content-type': 'application/json'}
result = []
img = face_recognition.load_image_file(img_path)
origin = Image.open(img_path)
locations = face_recognition.face_locations(img)

# 分割人脸并一一调用百度api
for i in range(len(locations)):
    result.append([])
    box = (locations[i][3], locations[i][0], locations[i][1], locations[i][2])
    face = origin.crop(box)
    output_buffer = BytesIO()
    pic_save_path = str(time.time())+img_path[img_path.rfind("."):]
    pic_save_path = os.path.join(BASE_DIR, "statics", "temp_image", pic_save_path)
    print(pic_save_path)
    face.save(pic_save_path)
    png = open(pic_save_path, 'rb')
    res = png.read()
    png.close()
    image = base64.b64encode(res).decode("ascii")
    params = '{"image":"%s","image_type":"BASE64","group_id_list":"admin","max_user_num":5,"match_threshold":60}' % image
    response = requests.post(request_url, data=params, headers=headers)
    print(response.json())
    if response.json()["error_msg"] == "SUCCESS":
        res_info = response.json()["result"]["face_list"][0]["user_list"]
        for j in range(len(res_info)):
            result[i].append({"id": res_info[j]["user_id"], "score": res_info[j]["score"]})
    else:
        result[i].append(response.json()["error_msg"])
    sleep(0.5)

# 结果格式化与可视化
recognition_result = []
time_now = time.time()
df = pd.DataFrame(result)
df.to_excel(os.path.join(BASE_DIR, 'statics', 'temp_image', '%f.xls' % time_now))
pil_image = Image.fromarray(img_path)
draw = ImageDraw.Draw(pil_image)
font_size = pil_image.size[0] // 50
ft = ImageFont.truetype(os.path.join(BASE_DIR, 'cv', 'files', 'arialuni.ttf'), font_size)
for i in range(len(locations)):
    box = (locations[i][3], locations[i][0], locations[i][1], locations[i][2])
    draw.rectangle(box, None, 'yellow', width=font_size // 8)
    draw.text((box[0:2]), str(i), "red", ft)
    recognition_result.append([])
    for j in range(len(result[i])):
        name = People.objects.filter(id=result[i][j]["id"])[0].name
        recognition_result[i].append(name)
        recognition_result[i].append(result[i][j]["score"])
    draw.text((box[0], box[1] - font_size), recognition_result[i][0], "red", ft)
img_path = os.path.join('temp_image', '%f.jpg' % time_now)
pil_image.save(os.path.join(BASE_DIR, 'statics', img_path))
return_dic= {'path': img_path, 'result': recognition_result}
return return_dic