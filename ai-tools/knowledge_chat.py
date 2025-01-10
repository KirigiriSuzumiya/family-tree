import requests
import json

app_id = json.load(open("config.json","r"))["chat_app_id"]
app_builder_token = json.load(open("config.json","r"))["chat_appbuilder_token"]

def get_conversation_id():
    url = "https://qianfan.baidubce.com/v2/app/conversation"
    
    payload = json.dumps({
        "app_id": app_id
    }, ensure_ascii=False)
    headers = {
        'Content-Type': 'application/json',
        'X-Appbuilder-Authorization': f'Bearer {app_builder_token}'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))
    
    return response.json()["conversation_id"]

def run_conversation(conversation_id: str, query: str):
    url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
    
    payload = json.dumps({
        "app_id": app_id,
        "conversation_id":conversation_id,
        "query": query,
        "stream": True
    }, ensure_ascii=False)
    headers = {
        'Content-Type': 'application/json',
        'X-Appbuilder-Authorization': f'Bearer {app_builder_token}'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"), stream=True)
    
    chunk_context = ""
    for chunk in response.iter_content(chunk_size=99999999, decode_unicode=True):
        if str(chunk).startswith("data:"):
            if chunk_context:
                yield json.loads(chunk_context)
            chunk_context = chunk[5:]
        else:
            chunk_context += chunk

def main():
    conversation_id = get_conversation_id()
    run_conversation(conversation_id=conversation_id, query="123")
    
    

if __name__ == '__main__':
    main()
