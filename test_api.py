import requests

url = "https://v3.football.api-sports.io/status"
headers = {
    'x-apisports-key': '7419e977170de5db2ea68791e952179f'
}
try:
    res = requests.get(url, headers=headers, verify=False)
    print("STATUS:", res.status_code)
    print(res.text)
except Exception as e:
    print(e)
