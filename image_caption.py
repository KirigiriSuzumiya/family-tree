import requests
import os
import numpy as np
import json
import time

huggingface_token = "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"


def caption_chat(img_path, ocr, face_info):
    API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {"Authorization": f"Bearer {huggingface_token}"}
    os.environ['CURL_CA_BUNDLE'] = ''
    with open(img_path, "rb") as f:
        data = f.read()
    while True:
        try:
            response = requests.post(API_URL, headers=headers, data=data, )
            break
        except:
            print("retry")
            time.sleep(0.6)
    caption_res = response.json()[0]["generated_text"]
    result = ocr.ocr(img_path, cls=True)
    print(len(result),len(result[0]),len(result[0][0]))
    bboxes = []
    text = []
    for i,res in enumerate(result[0]):
        bboxes.append(res[0]+[i])
        text.append(res[1])
    bboxes = sorted_boxes(np.array(bboxes))
    sorted_text = []
    for bbox in bboxes:
        index = bbox[-1]
        sorted_text.append(text[index][0])
    ocr_result = " ".join(sorted_text)
    prompt1 = get_prompt(ocr_result, caption_res, face_info)
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + get_access_token()
    payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": prompt1
            }
        ],
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    eb_result = response.json()["result"]
    return prompt1, eb_result, bboxes, sorted_text


def sorted_boxes(dt_boxes):
    """
    Sort text boxes in order from top to bottom, left to right
    args:
        dt_boxes(array):detected text boxes with shape [4, 2]
    return:
        sorted boxes(array) with shape [4, 2]
    """
    num_boxes = dt_boxes.shape[0]
    sorted_boxes = sorted(dt_boxes, key=lambda x: (x[0][1], x[0][0]))
    _boxes = list(sorted_boxes)

    for i in range(num_boxes - 1):
        for j in range(i, -1, -1):
            if abs(_boxes[j + 1][0][1] - _boxes[j][0][1]) < 10 and \
                    (_boxes[j + 1][0][0] < _boxes[j][0][0]):
                tmp = _boxes[j]
                _boxes[j] = _boxes[j + 1]
                _boxes[j + 1] = tmp
            else:
                break
    return _boxes


def get_prompt(ocr_result, desc, face_list):
    """
    Generate prompt from ocr_result and key
    """
    task_description = '你现在的任务是为我介绍一张包含单人或多人的相片并回答我提出的一些问题。我将会提供包括对相片的整体描述，出现人物的概述，以及相片中出现的文字等关键信息。\n\n'\
                       '你需要尝试从我提供的有限信息中理解这张相片中的人物为什么会一起拍照，以及从相片中的文字中找到相片是在何时何地拍摄的。\n\n'
    prompt = f"""{task_description}
        下面正式开始：

        相片整体概述：`{desc}`

        相片中的文字：`{ocr_result}`

        相片中出现的人物：`{face_list}`
        
        """
    return prompt


def get_access_token():
    """
    使用 API Key，Secret Key 获取access_token，替换下列示例中的应用API Key、应用Secret Key
    """
        
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=m0KDXW5zbVxjHy3UCQOX9f5R&client_secret=ha5uKeK1NTDbY03jIY8ANDwCXEKZRvjK"
    
    payload = json.dumps("")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json().get("access_token")