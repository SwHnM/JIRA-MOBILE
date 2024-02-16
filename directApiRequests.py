import requests
import base64

def full_comment(issue_key, username, password):

   
    auth_raw = f'{username}:{password}'
    auth_encode = auth_raw.encode("ascii") 
    auth_b64 = base64.b64encode(auth_encode)
    
    auth = auth_b64.decode("ascii")



    url = f"https://servicedesk.isha.in/rest/api/2/issue/{issue_key}/comment?expand=properties"
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    output = response.json()


    return output