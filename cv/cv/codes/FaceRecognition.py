import base64
import shutil
import time
from io import BytesIO

import face_recognition
import numpy as np
import os
import pandas as pd
import requests
from PIL import Image, ImageDraw, ImageFont
from ..settings import BASE_DIR
from django.shortcuts import render
from dbmodel.models import FaceImage, People
from dbmodel.models import Image as image_db
from django.contrib import messages
info_dict = {}
info =""

def initialing():
    return
    # 载入已保存的模型
    global info_dict
    info_dict = {}
    model_saving_path = os.path.join(BASE_DIR, 'cv', 'model')
    face_objs = FaceImage.objects.all()
    for face_obj in face_objs:
        path = face_obj.path
        name = path[:path.rfind('.')]
        path = os.path.join(model_saving_path, face_obj.path)
        info = np.load(path[:path.rfind('.')]+'.npy')
        info_dict[name] = info
    return_str = ""
    for i in info_dict.keys():
        return_str += i + ','
    return return_str

def face_matchng(path,request,tolerance=1):
    img_path = path
    # client_id 为官网获取的AK， client_secret 为官网获取的SK
    # 获取access_token
    global info
    info = "正在初始化"
    api_key = "jkyuzoYl4Cly99sEmxNMZog3"
    secret_key = "09UaoIt6Bu96g10Hjiyg2pnyW0QvRCrj"
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (
    api_key, secret_key)
    response = requests.get(host)
    if response:
        access_token = response.json()["access_token"]
    else:
        return 0


    result = []
    info = "正在分割人脸"
    try:    # 使用百度api分割人脸
        try:
            if request.POST["use_baidu"] == "yes":
                pass
            else:
                raise "NotUsingBaidu"
        except:
            image_obj = image_db.objects.get(path=os.path.basename(img_path))
            if not image_obj.use_baidu:
                raise "NotUsingBaidu"
        url = 'http://124.221.104.193/static/upload/' + os.path.basename(img_path)
        print("地址：", url)
        # 设置请求包体
        request_url = "https://aip.baidubce.com/rest/2.0/face/v3/detect"
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/json'}
        result = []
        params = '{"image":"%s","image_type":"URL","max_face_num":100}' % url
        response = requests.post(request_url, data=params, headers=headers)
        print(response.json())
        if response.json()["error_msg"] != "SUCCESS":
            raise "baiduExtractError"
        facelist = response.json()["result"]["face_list"]
        origin_locations = []
        locations = []
        for face in facelist:
            origin_locations.append(face["location"])
        face_list = origin_locations
        for i in range(len(face_list)):
            box = (face_list[i]["left"], face_list[i]["top"], face_list[i]["left"] + face_list[i]["width"],
                   face_list[i]["top"] + face_list[i]["height"])
            locations.append([box[1], box[2], box[3], box[0]])
        print("使用百度api分割人脸")
    except: # 使用face_recognition分割人脸
        img = face_recognition.load_image_file(img_path)
        locations = face_recognition.face_locations(img)
        print("使用face_recognition分割人脸")
    origin = Image.open(img_path)
    time_now = os.path.basename(img_path)[:os.path.basename(img_path).rfind('.')]
    file_type = os.path.basename(img_path)[os.path.basename(img_path).rfind('.'):]
    # 设置请求包体
    request_url = "https://aip.baidubce.com/rest/2.0/face/v3/multi-search"
    request_url = request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/json'}
    try:
        image_obj = image_db.objects.get(path=os.path.basename(img_path))
        image_obj.count = len(locations)
        image_obj.save()
    except:
        pass
    # 分割人脸并一一调用百度api
    for i in range(len(locations)):
        info = "正在识别第%d个人脸，共%d个" % (i, len(locations))
        result.append([])
        box = (locations[i][3], locations[i][0], locations[i][1], locations[i][2])
        face = origin.crop(box)
        output_buffer = BytesIO()
        pic_save_path = str(time_now) + "-" + str(i+1) + img_path[img_path.rfind("."):]
        pic_save_path = os.path.join(BASE_DIR, "statics", "temp_image", pic_save_path)
        print(pic_save_path)
        face.save(pic_save_path)
        png = open(pic_save_path, 'rb')
        res = png.read()
        png.close()
        image = base64.b64encode(res).decode("ascii")
        params = '{"image":"%s","image_type":"BASE64","group_id_list":"admin","max_user_num":5,"match_threshold":%d}' % (image,int(tolerance*100))
        response = requests.post(request_url, data=params, headers=headers)
        print(response.json())
        if response.json()["error_msg"] == "SUCCESS":
            res_info = response.json()["result"]["face_list"][0]["user_list"]
            for j in range(len(res_info)):
                result[i].append({"id": res_info[j]["user_id"], "score": res_info[j]["score"]})
        else:
            result[i].append(response.json()["error_msg"])
        time.sleep(0.5)

    # 结果格式化与可视化
    info = "正在整合信息"
    recognition_result = []
    df = pd.DataFrame(result)
    df.to_excel(os.path.join(BASE_DIR, 'statics', 'temp_image', time_now+'.xls'))
    pil_image = Image.open(img_path)
    draw = ImageDraw.Draw(pil_image)
    font_size = pil_image.size[0] // 50
    ft = ImageFont.truetype(os.path.join(BASE_DIR, 'cv', 'files', 'arialuni.ttf'), font_size)
    for i in range(len(locations)):
        box = (locations[i][3], locations[i][0], locations[i][1], locations[i][2])
        draw.rectangle(box, None, 'yellow', width=font_size // 8)
        draw.text((box[0:2]), str(i+1), "red", ft)
        recognition_result.append([])
        for j in range(len(result[i])):
            if result[i][j] == "match user is not found":
                name = "未知人脸"
                recognition_result[i].append([name, -1, 0])
            elif type(result[i][j]) == str:
                name = "人脸解析出错"
                recognition_result[i].append([name, -1, 0])
            elif type(result[i][j]) == dict:
                try:
                    name = People.objects.filter(id=result[i][j]["id"])[0].name
                    peo_id = result[i][j]["id"]
                    recognition_result[i].append([name, peo_id, result[i][j]["score"]])
                    if result[i][j]["score"] == 100:
                        draw.rectangle(box, None, 'lime', width=font_size // 8)
                except:
                    name = "本地库丢失id=%s" % result[i][j]["id"]
                    peo_id = result[i][j]["id"]
                    recognition_result[i].append([name, peo_id, result[i][j]["score"]])
                    if result[i][j]["score"] == 100:
                        draw.rectangle(box, None, 'lime', width=font_size // 8)
        if recognition_result[i][0][0] == "未知人脸" or recognition_result[i][0][0] == "人脸解析出错":
            continue
        draw.text((box[0], box[1] - font_size), str(recognition_result[i][0][0]), "red", ft)
    img_path = os.path.join('temp_image', time_now + file_type)
    pil_image.save(os.path.join(BASE_DIR, 'statics', img_path))
    return_dic = {'path': img_path, 'result': recognition_result}
    return return_dic


def dict_add(path, name):
    name_path = os.path.split(path)[-1]
    img_path = name_path[:name_path.find("-")]+name_path[name_path.rfind("."):]
    try:
        image_obj = image_db.objects.filter(path=img_path)[0]
    except:
        shutil.copy(os.path.join(BASE_DIR, "upload", img_path), os.path.join(BASE_DIR, "cv", "model_image", img_path))
        image_obj = image_db(path=img_path)
        image_obj.save()
    try:
        pic_save_path = os.path.join(BASE_DIR, 'cv', 'model_image', name+'@'+name_path)
        fpw = open(pic_save_path, "wb")
        fpr = open(path, "rb")
        for line in fpr:
            fpw.write(line)
        fpw.close()
        path = os.path.basename(pic_save_path)
        name = path[:path.find('@')]
        uploadtime = pic_save_path[pic_save_path.find('@') + 1:pic_save_path.rfind('-')]
        uploadtime = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(eval(uploadtime)))
        print(name, uploadtime, path, "\n")
        if People.objects.filter(name=name):
            people = People.objects.filter(name=name)[0]
        else:
            people = People(name=name)
            people.save()
        obj = FaceImage(name=people, path=path, upload_time=uploadtime, image=image_obj)
        obj.save()
        # 百度api上传
        # client_id 为官网获取的AK， client_secret 为官网获取的SK
        api_key = "jkyuzoYl4Cly99sEmxNMZog3"
        secret_key = "09UaoIt6Bu96g10Hjiyg2pnyW0QvRCrj"
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (api_key, secret_key)
        response = requests.get(host)
        if response:
            access_token = response.json()["access_token"]
        else:
            return "token获取失败"
        request_url = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add"
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/json'}
        png = open(pic_save_path, 'rb')
        res = png.read()
        png.close()
        image = base64.b64encode(res).decode("ascii")
        params = '{"image":"%s","image_type":"BASE64","group_id":"admin","user_id":"%d"}' % (image, people.id)
        headers = {'content-type': 'application/json'}
        response = requests.post(request_url, data=params, headers=headers)
        if response.json()["error_msg"] !="SUCCESS":
            return "人脸编码失败或图像已存在"
        else:
            obj.token = response.json()["result"]["face_token"]
            obj.logid = response.json()["log_id"]
            obj.save()
    except IndexError:
        print("人脸过于模糊，请提供清晰的正面照")
        return 0
    return 1


def face_show(image):
    face_landmarks_list = face_recognition.face_landmarks(image)
    pil_image = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_image)
    for face_landmarks in face_landmarks_list:
        facial_features = [
            'chin',
            'left_eyebrow',
            'right_eyebrow',
            'nose_bridge',
            'nose_tip',
            'left_eye',
            'right_eye',
            'top_lip',
            'bottom_lip'
        ]
        for facial_feature in facial_features:
            draw.line(face_landmarks[facial_feature], width=2)
    pil_image.show()


def dict_add_id(path, id):
    people = People.objects.filter(id=id)[0]
    name = people.name
    name_path = os.path.split(path)[-1]
    img_path = name_path[:name_path.find("-")]+name_path[name_path.rfind("."):]
    try:
        image_obj = image_db.objects.filter(path=img_path)[0]
    except:
        shutil.copy(os.path.join(BASE_DIR, "upload", img_path), os.path.join(BASE_DIR, "cv", "model_image", img_path))
        image_obj = image_db(path=img_path)
        image_obj.save()
    try:
        pic_save_path = os.path.join(BASE_DIR, 'cv', 'model_image', name+'@'+name_path)
        fpw = open(pic_save_path, "wb")
        fpr = open(path, "rb")
        for line in fpr:
            fpw.write(line)
        fpw.close()
        path = os.path.basename(pic_save_path)
        name = path[:path.find('@')]
        uploadtime = pic_save_path[pic_save_path.find('@') + 1:pic_save_path.rfind('-')]
        uploadtime = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(eval(uploadtime)))
        print(name, uploadtime, path, "\n")
        obj = FaceImage(name=people, path=path, upload_time=uploadtime, image=image_obj)
        obj.save()
        # 百度api上传
        # client_id 为官网获取的AK， client_secret 为官网获取的SK
        api_key = "jkyuzoYl4Cly99sEmxNMZog3"
        secret_key = "09UaoIt6Bu96g10Hjiyg2pnyW0QvRCrj"
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (api_key, secret_key)
        response = requests.get(host)
        if response:
            access_token = response.json()["access_token"]
        else:
            return "token获取失败"
        request_url = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add"
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/json'}
        png = open(pic_save_path, 'rb')
        res = png.read()
        png.close()
        image = base64.b64encode(res).decode("ascii")
        params = '{"image":"%s","image_type":"BASE64","group_id":"admin","user_id":"%d"}' % (image, people.id)
        headers = {'content-type': 'application/json'}
        response = requests.post(request_url, data=params, headers=headers)
        if response.json()["error_msg"] !="SUCCESS":
            return "人脸编码失败或图像已存在"
        else:
            obj.token = response.json()["result"]["face_token"]
            obj.logid = response.json()["log_id"]
            obj.save()
    except IndexError:
        print("人脸过于模糊，请提供清晰的正面照")
        return 0
    return 1



# dict_add(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\裨益知 W. L. Beard\Young Willard L. Beard from 1894 letter.jpg","W.L.Beard")
# dict_add(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\face\Young Ellen Lucy Kinney (Mrs. Beard) from 1894 letter-1.jpg","E.L.Kinney")
# dict_add(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\face\model\1891-1894 W. L. Beard 04254v-1.jpg", "W.L.Beard-y")
# dict_add(r"C:\Users\boyif\Desktop\paddle\re_pic\Dr. and Mrs. Baldwin missionaries 1847-1895 (Caleb C. and Harriet F. Baldwin) (from Jill Elmer Jackson - 1894 letter)-1.jpg","Mrs.Baldwin")
# face_matchng(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\裨益知 W. L. Beard\1900 - Willard L. Beard and Ellen are in the middle.jpg")
# face_matchng(r"F:\同步数据\家·谱：鼓岭外人社区的形成与谱系研究\裨益知 W. L. Beard\1900 - Willard L. Beard sits in the middle seated next to Ellen and Ding Ming Uong next to Ellen (from 1900 letter).jpg")
