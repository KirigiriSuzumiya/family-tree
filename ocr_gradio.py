import numpy as np
import gradio as gr
import os
import requests
import base64
import cv2
import time
import pandas as pd
from paddleocr import PaddleOCR
import json
import ocr_chat
from image_caption import caption_chat
from baiduImage import Crawler


auth = json.load(open("config.json","r"))
api_key = auth["face_api_key"]
secret_key = auth["face_secret_key"]
# Paddleocr目前支持的多语言语种可以通过修改lang参数进行切换
# 例如`ch`, `en`, `fr`, `german`, `korean`, `japan`
ocr_engine = PaddleOCR(lang="ch", use_angle_cls=False, rec_batch_num=8,
                       rec_model_dir="./ch_PP-OCRv4_rec_server_infer")  # need to run only once to download and load model into memory

max_face_box = 30
def face_recognize(image,ocr_key, method, search_check, peo_id):
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    filename=str(time.time())+".jpg"
    path = os.path.join("cv","upload",filename)
    cv2.imwrite(path, image)
    base64_str = cv2.imencode('.jpg',image)[1].tobytes()
    base64_str = base64.b64encode(base64_str)
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
    
    params = {"image":base64_str,
            "image_type":"BASE64",
            "group_id_list": "admin",
            "max_face_num":max_face_box}
    response = requests.post(request_url, data=params, headers=headers)
    result = response.json()["result"]
    face_token = []
    bboxs = []
    box_image = image.copy()
    for i, face in enumerate(result["face_list"]):
        face_token.append(face["face_token"])
        token = face["face_token"]
        location = face["location"]
        bbox = [int(location["left"]), int(location["top"]), int(location["left"]+location["width"]), int(location["top"]+location["height"])]
        box_image = cv2.rectangle(box_image,tuple(bbox[:2]),tuple(bbox[2:]),(0,0,255),thickness=2)
        box_image = cv2.putText(box_image, str(i+1), bbox[:2],cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),thickness=2)
        bboxs.append([bbox, "face:"+str(i+1)])
    path = os.path.join("cv","cv","model_image",filename)
    cv2.imwrite(path, box_image)
    result = {}
    if search_check:
        for i, token in enumerate(face_token):
            face_info = {}
            face_info["token"] = token
            face_info["bbox"] = bboxs[i]
            face_info["image"] = image[bboxs[i][0][1]:bboxs[i][0][3], bboxs[i][0][0]:bboxs[i][0][2]]
            face_info["image"] = cv2.cvtColor(face_info["image"], cv2.COLOR_BGR2RGB)
            face_info["user_list"] = [{"user_id":str(int(peo_id)),"score":100}]
            result[i] = face_info
    else:
        for i, token in enumerate(face_token):
            face_info = {}
            face_info["token"] = token
            face_info["bbox"] = bboxs[i]
            face_info["image"] = image[bboxs[i][0][1]:bboxs[i][0][3], bboxs[i][0][0]:bboxs[i][0][2]]
            face_info["image"] = cv2.cvtColor(face_info["image"], cv2.COLOR_BGR2RGB)
            request_url = "https://aip.baidubce.com/rest/2.0/face/v3/search"
            request_url = request_url + "?access_token=" + access_token
            headers = {'content-type': 'application/json'}
            params = {"image":token,
                    "image_type":"FACE_TOKEN",
                    "group_id_list": "admin",
                    "max_user_num": 5
                    }
            response = requests.post(request_url, data=params, headers=headers)
            response = response.json()["result"]["user_list"]
            face_info["user_list"] = response
            result[i] = face_info
            time.sleep(0.6)
    face_count = len(bboxs)
    url = "http://localhost:80/image_obj_ini"
    payload = {'file_name': filename,"face_count":face_count}
    response = requests.request("POST", url, data=payload)
    image_id = response.json()
    fast_link = f"### Fast link to family-tree Image Page:[click me to `{image_id['file_name']}`](http://nenva.com/pic_info/{image_id['file_name']})"
    # image_id = 0
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    yield [image, bboxs], result, gr.update(choices=[str(i+1) for i in range(face_count)], value="1"), \
           gr.update(visible=False),"",image_id, "", fast_link
    if method == "Face+Ocr+Chat":
        gr.Info("Face recognization has now completed, please wait until OCR complete")
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        global ocr_engine
        value, ocr_bbox, text = ocr_chat.work_flow(image, ocr_key, ocr_engine)
        temp = 0
        text_out = ""
        for i, ocr in enumerate(ocr_bbox):
            bboxs.append([[int(ocr[0][0]),int(ocr[0][1]),
                            int(ocr[2][0]),int(ocr[2][1])], 
                            text[i]])
            if ocr[0][0] > temp:
                text_out += text[i] + " "
            else:
                text_out += "\n" + text[i]
            temp = ocr[0][0]
        if value.get("姓名"):
            ocr_name = value["姓名"]
        else:
            ocr_name = ""
        df = pd.DataFrame([list(value.values())],columns=list(value.keys()))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        yield [image, bboxs], result, gr.update(choices=[str(i+1) for i in range(face_count)], value="1"),\
                gr.update(value=df,visible=True), ocr_name, image_id, text_out, fast_link
        

def chat_fun(msg, history):
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token=" + ocr_chat.get_access_token()
    payload = []
    for i in history:
        payload.append({"role": "user",
                        "content": i[0]})
        payload.append({"role": "assistant",
                        "content": i[1]})
    payload.append({"role": "user",
                        "content": msg})
    payload = {"messages":payload}
    payload = json.dumps(payload)
    # print(payload)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.json())
    eb_result = response.json()["result"]
    history.append([msg, eb_result])
    return "", history


def chat_fun_knowledge(msg, history, resource_info):
    url = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/plugin/0qmhz6shhxzvdz71/?access_token=' + ocr_chat.get_access_token()
    payload = []
    for i in history:
        payload.append({"role": "user",
                        "content": i[0]})
        payload.append({"role": "assistant",
                        "content": i[1]})
    # payload.append({"role": "user",
    #                     "content": msg})
    payload = {"history": payload,
               "query": msg,
               "verbose":True,}
    payload = json.dumps(payload)
    # print(payload)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    eb_result = response.json()["result"]
    history.append([msg, eb_result])
    file_names = []
    if not resource_info:
        resource_info = ""
    for i in response.json()["meta_info"]["response"]["result"]["responses"]:
        file_name = i["docName"]
        if file_name in file_names:
            continue
        else:
            file_names.append(file_name)
        file_content = open(f"/home/no_prompt/{file_name}").read()
        resource_info +=f"""<details> <summary>{file_name}</summary>
            {file_content}
            </details>
        """   
    return "", history, resource_info


def chat_init(img_path, additional_info):
    global ocr_engine
    image = cv2.imread(img_path)
    with open(img_path,"rb") as fp:
        base64_str = fp.read()
    base64_str = base64.b64encode(base64_str)
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
    
    params = {"image":base64_str,
            "image_type":"BASE64",
            "group_id_list": "admin",
            "max_face_num":max_face_box}
    response = requests.post(request_url, data=params, headers=headers)
    result = response.json()["result"]
    face_token = []
    bboxs = []
    for i, face in enumerate(result["face_list"]):
        face_token.append(face["face_token"])
        token = face["face_token"]
        location = face["location"]
        bbox = [int(location["left"]), int(location["top"]), int(location["left"]+location["width"]), int(location["top"]+location["height"])]
        bboxs.append([bbox, "face:"+str(i+1)])
    result = {}
    face_list = []
    for i, token in enumerate(face_token):
        face_info = {}
        face_info["token"] = token
        face_info["bbox"] = bboxs[i]
        face_info["image"] = image[bboxs[i][0][1]:bboxs[i][0][3], bboxs[i][0][0]:bboxs[i][0][2]]
        face_info["image"] = cv2.cvtColor(face_info["image"], cv2.COLOR_BGR2RGB)
        request_url = "https://aip.baidubce.com/rest/2.0/face/v3/search"
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/json'}
        params = {"image":token,
                "image_type":"FACE_TOKEN",
                "group_id_list": "admin",
                "max_user_num": 5
                }
        response = requests.post(request_url, data=params, headers=headers)
        response = response.json()["result"]["user_list"]
        face_info["user_list"] = response
        result[i] = face_info
        if response[0]["score"] >=90:
            url = "http://localhost:80/id2name"
            payload = {'id': response[0]["user_id"]}
            response = requests.request("POST", url, data=payload)
            face_list.append(response.json()['name'])
            bboxs[i][1]= "face:"+response.json()['name']
        time.sleep(0.6)
    prompt, response, ocr_bbox,text = caption_chat(img_path, ocr_engine, face_list, additional_info)
    for i, ocr in enumerate(ocr_bbox):
        bboxs.append([[int(ocr[0][0]),int(ocr[0][1]),
                        int(ocr[2][0]),int(ocr[2][1])], 
                        text[i]])
    next_chat = f"根据关键词{response}尝试去联系这张相片中可能的人物社交与建筑关系，并向我介绍可能的拍摄地点。"
    return [image,bboxs], [[prompt,response]], next_chat


with gr.Blocks(title="Face+OCR+Chat demo") as demo:
    # UI part
    image_id = gr.State(None)
    face_list = gr.State(dict())
    gr.Markdown("# FACE-OCR-CHAT demo")
    gr.Markdown("development edition, any question please refer to <boyifan1@126.com>")
    gr.Markdown("""Features: 
                - Using **BaiduAPI** for Face Recognization
                - Using **PP-OCR v4** for OCR
                - Using **ERNIE-Bot-turbo** for information extraction and chat
                """)
    with gr.Tab("Information Extract"):
        with gr.Column():
            with gr.Row():
                search_check = gr.Checkbox(label="Search Image from web",
                            info="if you want to use this, you should fill the people id below first")
                search_url = gr.Radio(label="Image from BaiduImage",visible=False)
                
            gr.Markdown("Notice: Whenever you click recognize button, image will be saved to database.")
            with gr.Row():
                with gr.Column():
                    input_image = gr.Image(source="upload", type="numpy")
                    with gr.Row():
                        # method = gr.Radio(label="recognizing method", choices=["Segement only","Face only","Face+Ocr+Chat"], value="Segement only",
                        #                 info="we use PP-OCRv4 and ERNIE-Bot-turbo for ocr and information extraction")
                        method = gr.Radio(label="recognizing method", choices=["Face only","Face+Ocr+Chat"], value="Face only",
                                        info="we use PP-OCRv4 and ERNIE-Bot-turbo for ocr and information extraction")
                        # up_sample = gr.Radio(label="up sample", choices=["1.0x","2.0x","4.0x"], value="1.0x",
                        #                 info="scale of up-sample and denoise,using 1.0x will skip the preprocess")
                    with gr.Row():
                        ocr_key = gr.Textbox(label="ocr keywords", value="姓名，籍贯", 
                                            info="LLM will find the information you need according to keywords given below")
                        ocr_output = gr.Textbox(interactive=False,label="ocr output",max_lines=5,
                                                info="raw output of ocr, you can get text without cleaning from here")
                with gr.Column():
                    faceoutput = gr.AnnotatedImage()
            btn = gr.Button("recognize",variant="primary")
            with gr.Row():
                face_image = gr.Image(label="chosen face",interactive=False)
                with gr.Column():
                    face_index = gr.Dropdown(label="face index",
                                            info="select face from image, or you can refesh this easily by simply click the  bounding box above")
                    face_recog = gr.Radio(label="face result",info="recognization result from database")
                    with gr.Row():
                        create_name = gr.Textbox(label="new name")
                                                #  info="if you want to create a new person in database, you need to fill this. If you are using ocr with keywords 姓名, this will be filled auto.")
                        create_new_btn = gr.Button("create new person",size='sm',interactive=True)
                with gr.Column():
                    fast_link = gr.Markdown("### Fast link to family-tree Image Page:[click me to list page](http://nenva.com/piclist)")
                    face_name = gr.Markdown("### Fast link to family-tree Person Page:[click me to list page](http://nenva.com/namelist)")
                    face_id = gr.Number(label="person id", info="person id from database, auto filled most of the time, you can also edit it if needed.")
                    temp_output = gr.Dataframe(visible=False)
            upload_btn = gr.Button("upload", interactive=True)
            btn.click(face_recognize, 
                    inputs=[input_image, ocr_key, method, search_check,face_id], 
                    outputs=[faceoutput,face_list, face_index, temp_output, create_name, image_id, ocr_output, fast_link])
    with gr.Tab("ChatBot"):
        with gr.Tab("Knowledge Base"):
            with gr.Column():
                gr.Markdown("Notice: This module is under development and may be unstable,please report any error you meet to make our service better.")
                gr.Markdown("- TEXT Knowledge based on wiki_doc_20230921 is only for evaluation test, real-time update will be supported in the near future.")
                gr.Markdown("- Image Knowledge based on OCR and Face Recognition")
                with gr.Accordion("Image Caption Embedding"):
                    with gr.Row():
                        input_image_bot = gr.Image(source="upload", type="filepath")
                        faceoutput_bot = gr.AnnotatedImage()
                    additional_info = gr.Textbox(placeholder="Some additional information you want to mentioned")
                    bot_btn = gr.Button("Extract Info from the Image", variant="primary")
                with gr.Row():
                    chatbot_knowledge = gr.Chatbot(height=800, scale=2,
                                                   label="LLM chatbot", info="say something and try it out!")
                    with gr.Accordion("Knowledge Source"):
                        knowledge_source = gr.HTML(height=800, label="Knowledge Source", 
                                                info="Docs hit by embedding match.", show_label=True)
                msg_knowledge = gr.Textbox(label="input your words", info="push 'ENTER' to submit")
                msg_knowledge.submit(chat_fun_knowledge, 
                                     [msg_knowledge, chatbot_knowledge, knowledge_source], 
                                     [msg_knowledge, chatbot_knowledge, knowledge_source])
                bot_btn.click(chat_init,
                              inputs=[input_image_bot, additional_info], 
                              outputs=[faceoutput_bot, chatbot_knowledge, msg_knowledge])
                clr_btn_knowledge = gr.Button("Clear")
                clr_btn_knowledge.click(lambda: [None,None,None], None, [msg_knowledge, chatbot_knowledge, knowledge_source])
        with gr.Tab("Normal Chat"):
            with gr.Column():
                gr.Markdown("Notice: This module is under development and may be unstable,please report any error you meet to make our service better.")
                chatbot = gr.Chatbot(height=800, label="LLM chatbot", info="say something and try it out!")
                msg = gr.Textbox(label="input your words", info="push 'ENTER' to submit")
                msg.submit(chat_fun, [msg,chatbot], [msg, chatbot])
                clr_btn = gr.Button("Clear")
                clr_btn.click(lambda: [None,None], None, [msg, chatbot])



    # listener
    input_image.upload(lambda: False,None,search_check)
    def web_image_select(search_url):
        if not search_image:
            return gr.update(visible=True)
        res = requests.get(search_url)
        img = cv2.imdecode(np.frombuffer(res.content, np.uint8), cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        return img
    search_url.change(web_image_select,search_url,input_image)


    def search_image(peo_id, search_check):
        if not search_check:
            return gr.update(visible=False,choices=None,value=None)
        try:
            url = "http://localhost:80/id2name"
            payload = {'id': int(peo_id)}
            response = requests.request("POST", url, data=payload)
            name = response.json()['name']
        except:
            gr.Error("Please input correct id first!")
            return None
        crawler = Crawler(0.1)  # 抓取延迟为 0.1
        print(name)
        try:
            image_urls = crawler.start(name)
        except:
            gr.Error("image search failed")
            return None
        if len(image_urls)>10:
            image_urls=image_urls[:10]
        return gr.update(choices=image_urls,visible=True,value=image_urls[0]) 
    search_check.change(search_image,[face_id,search_check],search_url)


    def click_anno(evt: gr.SelectData):
        if "face" in evt.value:
            label = evt.value
            return gr.update(value=label[label.find(":")+1:]) 
        else:
            return gr.update(visible=True)
    faceoutput.select(click_anno,outputs=face_index)


    def create_person(name):
        url = "http://localhost:80/peo_obj_ini"
        if name is None:
            return None
        payload = {'name': name}
        response = requests.request("POST", url, data=payload)
        id = str(response.json()) + ":" +"new"
        return gr.update(value=id, choices=face_recog.choices+[id])
    create_new_btn.click(create_person,
                         inputs=create_name,
                         outputs=face_recog)


    def upload_face(image_id, peo_id, face_index, face_list):
        filename = image_id["file_name"]
        url = "http://localhost:80/id2name"
        payload = {'id': int(peo_id)}
        response = requests.request("POST", url, data=payload)
        filename = f"{response.json()['name']}@{filename[:filename.rfind('.')]}-{str(face_index)+filename[filename.rfind('.'):]}"
        path = os.path.join("cv","cv","model_image",filename)
        img_save = cv2.cvtColor(face_list[int(face_index)-1]["image"], cv2.COLOR_RGB2BGR)
        cv2.imwrite(path, img_save)
        url = "http://localhost:80/face_obj_ini"
        payload = {'image_id': int(image_id["id"]),
                   'name_id':int(peo_id),
                   'path':filename,
                   'token':face_list[int(face_index)-1]["token"]}
        response = requests.request("POST", url, data=payload)
        if response.status_code == 200:
            gr.Info("Upload seccess")
        else:
            gr.Error("Upload failed")
        host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (api_key, secret_key)
        response = requests.get(host)
        if response:
            access_token = response.json()["access_token"]
        else:
            return "token获取失败"
        request_url = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add"
        request_url = request_url + "?access_token=" + access_token
        headers = {'content-type': 'application/json'}
        params = {"image":face_list[int(face_index)-1]["token"],
                  "image_type":"FACE_TOKEN",
                  "group_id":"admin",
                  "user_id":peo_id}
        headers = {'content-type': 'application/json'}
        response = requests.post(request_url, data=params, headers=headers)
        if response.json()["error_msg"] !="SUCCESS":
            gr.Error("Upload to baidu failed")
        else:
            gr.Info("Upload to baidu success")
    upload_btn.click(upload_face,
                     inputs=[image_id, face_id, face_index, face_list])
        


    def index_change(index,face_list):
        index_update = gr.update(visible=True)
        image_update = gr.update(value=face_list[int(index)-1]["image"],visible=True)
        peo_id = [res["user_id"]+":"+ "%.2f" % (res["score"]/100) for res in face_list[int(index)-1]["user_list"]]
        reco_update = gr.update(choices=peo_id, value=peo_id[0],visible=True)
        return index_update, image_update, reco_update
    face_index.change(index_change, 
                      inputs=[face_index, face_list], 
                      outputs=[face_index, face_image, face_recog])


    def recogn_change(radio):
        return gr.update(value=int(radio[:radio.find(":")]))
    face_recog.change(recogn_change,
                     inputs=face_recog,
                     outputs=face_id)
    

    def id_change(peo_id):
        url = "http://localhost:80/id2name"
        payload = {'id': int(peo_id)}
        response = requests.request("POST", url, data=payload)
        name_update = gr.update(value=f"### Fast link to family-tree Person Page:[click me to `{response.json()['name']}`](http://nenva.com/facelist/{int(peo_id)})")
        return name_update
    face_id.change(id_change, 
                   inputs=face_id, 
                   outputs=face_name)

        
    
demo.queue(concurrency_count=3)
demo.launch(server_name="0.0.0.0",server_port=2333, show_error=True, auth=("admin", "kuliang2023"))