import numpy as np
import json
import requests
import os


auth = json.load(open("config.json","r"))

def traverse_nested_lists(lst, result):
    """
    Traverse a nested list recursively
    """
    for item in lst:
        if isinstance(item, list):
            traverse_nested_lists(item, result)
        else:
            result.append(item)
    return result


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

def get_prompt(ocr_result, key=None, few_shot_info=''):
    """
    Generate prompt from ocr_result and key
    """
    task_description = '你现在的任务是从OCR文字识别的结果中提取关键词列表中每一项对应的关键信息。OCR的文字识别结果使用```符号包围，包含所识别出来的文字，\
            顺序在原始图片中从左至右、从上至下。我指定的关键词列表使用[]符号包围。请注意OCR的文字识别结果可能存在长句子换行被切断、不合理的分词、\
            文字被错误合并等问题，你需要结合上下文语义进行综合判断，以抽取准确的关键信息。\
            在返回结果时使用JSON字典格式，包含多个key-value对，key值为我指定的关键词(字符串类型)，value值为所抽取的结果(字符串类型)。即便只有一个关键字也请保持"key:value"的字典格式完整。\
            如果认为OCR识别结果中没有关键信息key，则将value赋值为“未找到相关信息”。请只输出JSON字典格式的结果，不要包含其它多余文字！'
    prompt = f"""{task_description}
        下面正式开始：
        OCR文字：```{ocr_result}```
        关键词列表：[{key}]。"""
    return prompt

def get_access_token():
    from qianfan.resources.console.iam import IAM
    """
    使用 API Key，Secret Key 获取access_token，替换下列示例中的应用API Key、应用Secret Key
    """
    os.environ["QIANFAN_ACCESS_KEY"] = auth['chat_api_key']
    os.environ["QIANFAN_SECRET_KEY"] = auth['chat_secret_key']
    # 调用创建bearerToken接口，获取bearerToken
    response = IAM.create_bearer_token(expire_in_seconds=86400)

    return str(response.body.get("token"))


def work_flow(img_path, key, ocr):
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
    prompt1 = get_prompt(ocr_result, key=key)
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
    print(eb_result)
    try:
        if "json" in eb_result:
            eb_result = eb_result.replace("```", "").replace(
                "json", "")
            value = json.loads(eb_result)
            if type(value) is list:
                value = value[0]
        elif type(eval(eb_result)) is dict:
            value = eval(eb_result)
        else:
            value = {"error":"未找到关键信息"}
    except:
        value={"error":f"返回格式可能有误：{eb_result}"}
    return value, bboxes, sorted_text
    # return bboxes, sorted_text