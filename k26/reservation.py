import requests
import bs4
import chardet
from datetime import datetime, timezone, timedelta
import time

url = "http://k-26.com"
board_url = "/reserved_community/board_list.php?cp=%i"
post_url = "/reserved_community/board_read.php?rn=%i&ss="
today = time.time()

# make thoese to class
def get_service():
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_data(res):
    saved_info = {}
    link = res.find('a')
    if link:
        post_link = link.get('href')
        if not post_link.startswith("javascript"):
            post = requests.get(url + post_link)
            soup = bs4.BeautifulSoup(post.content.decode('utf-8', 'replace'),
                                    'html.parser', from_encoding='utf-8')
            content = soup.find_all("td", class_="reserved_info_box", attrs={"width": "70%"})
            info_list = []
            for c in content:
                infos = c.text.split('<b>')[0].split('\n')
                for info in infos:
                    info_text =info.replace(' ', '').replace('\r', '')
                    if info_text:
                        info_list.append(info_text)
            try:
                if '결제완료' in info_list:
                    key = '예약완료'
                else:
                    key = '예약중'
                if len(info_list) > 6:
                    date = datetime.strptime(info_list[0].split('(')[0], '%Y-%m-%d')
                    time_start, time_end = 0, 0
                    if info_list[5] == "이용시간":
                        time_start, time_end = info_list[6].split("~")
                        time_start = int(time_start.split(":")[0])
                        time_end = int(time_end.split(":")[0])-1
                    diving_type = "free"
                    if info_list[3].strip() == "이용종목":
                        if info_list[4].strip() == "스킨스쿠버":
                            diving_type = "diving"
                    if date.timestamp() < today-(60*60*24):
                        return '', {}
                    else:
                        future_date = True
                        saved_info[info_list[0]] = {}
                        for time in range(time_start, time_end+1):
                            saved_info[info_list[0]][time] = {"diving": {'예약완료': 0, '예약중':0},
                                                        "free": {"예약완료":0, "예약중": 0}}
                            saved_info[info_list[0]][time][diving_type][key] += int(info_list[8].split('명')[0])
                        return info_list[0], saved_info[info_list[0]]
            except Exception as e:
                print(e)
    return '', {}

if __name__ == "__main__":
    saved_info = {}
    exist = True
    num = 1
    while exist:
        result = requests.get(url + board_url%num)
        soup = bs4.BeautifulSoup(result.content.decode('utf-8', 'replace'), 'html.parser', from_encoding='utf-8')
        reservations = soup.find_all(id="tit_4")
        future_date = False
        for res in reservations:
            key, values = get_data(res)
            for value in values:
                if not key in saved_info:
                    saved_info[key] = {}
                if not value in saved_info[key]:
                    saved_info[key][value] = values[value]
                else:
                    saved_info[key][value]["diving"]['예약완료'] += values[value]["diving"]['예약완료']
                    saved_info[key][value]["free"]['예약완료'] += values[value]["free"]['예약완료']
                    saved_info[key][value]["diving"]['예약중'] += values[value]["diving"]['예약중']
                    saved_info[key][value]["free"]['예약중'] += values[value]["free"]['예약중']
        num += 1
        if num > 10:
            exist = False
        else:
            print(num)

    for info in saved_info:
        print(info)
        for x in range(0,24):
            if x in saved_info[info]:
                print(x, "다이빙", saved_info[info][x]["diving"])
                print(x, "프리다이빙", saved_info[info][x]["free"])

