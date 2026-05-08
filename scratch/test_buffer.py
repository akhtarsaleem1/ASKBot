import requests
from askbot.config import get_settings

def test():
    s = get_settings()
    res = requests.get('https://api.bufferapp.com/1/user.json', headers={'Authorization': 'Bearer ' + s.buffer_api_key})
    print("REST API Status:", res.status_code)
    try:
        print(res.json())
    except:
        pass
        
if __name__ == '__main__':
    test()
