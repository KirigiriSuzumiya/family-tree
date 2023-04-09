import face_recognition
from PIL import Image,ImageDraw,ImageFont
import glob
import os
from pathlib import Path
from dbmodel.models import FaceImage, People
from dbmodel.models import Image as image_db
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
fp = open(os.path.join(BASE_DIR, "baidu_key.txt"))
api_key, secret_key = fp.readlines()[0:2]

def extractor(img_path):
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    image = face_recognition.load_image_file(img_path)
    origin = Image.open(img_path)
    locations = face_recognition.face_locations(image)
    # 保存合照人头画框
    pil_image = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_image)
    font_size = pil_image.size[0] // 30
    ft = ImageFont.truetype(os.path.join(BASE_DIR, 'cv', 'files', 'arialuni.ttf'), font_size)
    face_list = locations
    for i in range(len(face_list)):
        box = (face_list[i][3], face_list[i][0], face_list[i][1], face_list[i][2])
        font_size = int(abs(box[0] - box[2]) // 3)
        ft = ImageFont.truetype(os.path.join(BASE_DIR, 'cv', 'files', 'arialuni.ttf'), font_size)
        draw.rectangle(box, None, 'yellow')
        draw.text((box[0:2]), str(i+1), "red", ft)
    img_path = os.path.join(BASE_DIR, 'cv', 'model_image', os.path.split(img_path)[-1])
    pil_image.save(img_path)
    img_path = os.path.join(BASE_DIR, 'statics', 'temp_image', os.path.split(img_path)[-1])
    image = image_db(path=os.path.split(img_path)[-1], count=len(face_list))
    image.save()
    # 保存各个人头大头贴
    count = 1
    for location in locations:
        box = (location[3], location[0], location[1], location[2])
        face = origin.crop(box)
        save_path = img_path[0:img_path.rfind('.')]+'-'+str(count)+img_path[img_path.rfind("."):]
        face.save(save_path)
        #print(save_path+" saved!")
        count += 1
    return count-1


def baidu_extractor(img_path):
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    url = 'http://43.143.68.17/static/upload/'+img_path
    print("地址：", url)
    img_path = os.path.join(BASE_DIR, "upload", img_path)
    # client_id 为官网获取的AK， client_secret 为官网获取的SK
    # 获取access_token
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (
    api_key, secret_key)
    response = requests.get(host)
    if response:
        access_token = response.json()["access_token"]
    else:
        return 0

    # 设置请求包体
    request_url = "https://aip.baidubce.com/rest/2.0/face/v3/detect"
    request_url = request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/json'}
    result = []
    params = '{"image":"%s","image_type":"URL","max_face_num":100}' % url
    response = requests.post(request_url, data=params, headers=headers)
    print(response.json())
    if response.json()["error_msg"] != "SUCCESS":
        return 0
    facelist = response.json()["result"]["face_list"]
    locations = []
    origin = Image.open(img_path)
    for face in facelist:
        locations.append(face["location"])
    # 保存合照人头画框
    pil_image = Image.open(img_path)
    draw = ImageDraw.Draw(pil_image)
    font_size = pil_image.size[0] // 30
    ft = ImageFont.truetype(os.path.join(BASE_DIR, 'cv', 'files', 'arialuni.ttf'), font_size)
    face_list = locations
    for i in range(len(face_list)):
        box = (face_list[i]["left"], face_list[i]["top"], face_list[i]["left"] + face_list[i]["width"],face_list[i]["top"] + face_list[i]["height"])
        font_size = int(abs(box[0]-box[2]) // 3)
        ft = ImageFont.truetype(os.path.join(BASE_DIR, 'cv', 'files', 'arialuni.ttf'), font_size)
        draw.rectangle(box, None, 'yellow')
        draw.text((box[0:2]), str(i +1), "red", ft)
    img_path = os.path.join(BASE_DIR, 'cv', 'model_image', os.path.split(img_path)[-1])
    pil_image.save(img_path)
    img_path = os.path.join(BASE_DIR, 'statics', 'temp_image', os.path.split(img_path)[-1])
    image = image_db.objects.get(path=os.path.split(img_path)[-1])
    image.count = len(locations)
    image.use_baidu = True
    image.save()
    # 保存各个人头大头贴
    count = 1
    for location in locations:
        box = (location["left"], location["top"], location["left"]+location["width"], location["top"]+location["height"])
        face = origin.crop(box)
        save_path = img_path[0:img_path.rfind('.')] + '-' + str(count) + img_path[img_path.rfind("."):]
        face.save(save_path)
        # print(save_path+" saved!")
        count += 1
    return count - 1

