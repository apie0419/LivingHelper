import re
import time
import random
import requests
from bs4 import BeautifulSoup
from linebot.v3.messaging.models.push_message_request import PushMessageRequest
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    TextMessage,
    FlexBubble,
    FlexCarousel,
    FlexMessage
)

configuration = Configuration(
    access_token = "<LINE_ACCESS_TOKEN>",
    host = "https://api.line.me"
)

group_id = "<GROUP_ID>"

def get_mtr_lines():
    return [162, 148, 100]

def get_region():
    return [1, 3]

def get_params(mrtline, region):
    mrt = {
        162: [4231, 4232, 4184, 4233, 4234, 4221],
        148: [4244, 4184, 4245, 4248, 4249],
        100: [4187, 4190, 4189]
    }
    wanted_columns = ["title", "post_id", "floor_str", "price", "price_unit", "photo_list", "surrounding"]
    filter_params = {
        "region": str(region),
        "mrtcoods": ",".join(list(map(str, mrt[mrtline]))),
        "searchtype": "4",
        "rentprice": "12000,22000",
        "showMore": "1",
        "multiNotice": "not_cover",
        "other": "near_subway"
    }
    sort_params = {
        "order": "posttime",
        "orderType": "desc"
    }
    return filter_params, sort_params

def get_visited_houses():
    post_ids = list()
    with open("visited_houses.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace("\n", "")
            post_ids.append(int(line))
    return post_ids

def search_houses(filter_params=None, sort_params=None, page=1):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.68",
    }
    house_list = []

    s = requests.Session()
    url = "https://rent.591.com.tw/"
    r = s.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    token_item = soup.select_one("meta[name=\"csrf-token\"]")

    headers["X-CSRF-TOKEN"] = token_item.get("content")

    url = "https://rent.591.com.tw/home/search/rsList"
    params = "is_format_data=1&is_new_list=1&type=1"
    if filter_params:
        params += "".join([f"&{key}={value}" for key, value, in filter_params.items()])
    else:
        params += "&region=1&kind=0"
        
    s.cookies.set("urlJumpIp", filter_params.get("region", "1") if filter_params else "1", domain=".591.com.tw")

    if sort_params:
        params += "".join([f"&{key}={value}" for key, value, in sort_params.items()])
    
    params += f"&firstRow={page*30}"
    
    r = s.get(url, params=params, headers=headers)
    if r.status_code != requests.codes.ok:
        print("request failed", r.status_code)
        return []

    data = r.json()
    house_list.extend(data["data"]["data"])
    
    time.sleep(random.uniform(2, 5))

    return house_list

def get_flex_bubble(title, floor, price, mrt, url, first_img):
    bubble = {
      "type": "bubble",
      "size": "giga",
      "hero": {
        "type": "image",
        "url": first_img,
        "size": "full",
        "aspectMode": "cover",
        "aspectRatio": "320:213"
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": title,
            "weight": "bold",
            "size": "md",
            "wrap": True
          },
          {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                  {
                    "type": "text",
                    "text": "價錢: " + price,
                    "wrap": True,
                    "color": "#8c8c8c",
                    "size": "sm",
                    "flex": 5,
                    "weight": "bold"
                  },
                  {
                    "type": "text",
                    "text": "樓層: " + floor,
                    "flex": 5,
                    "size": "sm",
                    "color": "#8c8c8c",
                    "wrap": True,
                    "weight": "bold"
                  },
                  {
                    "type": "text",
                    "text": "最近捷運站: " + mrt,
                    "flex": 5,
                    "size": "sm",
                    "color": "#8c8c8c",
                    "weight": "bold",
                    "wrap": True
                  }
                ]
              }
            ]
          }
        ],
        "spacing": "sm",
        "paddingAll": "lg"
      },
      "footer": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "button",
            "action": {
              "type": "uri",
              "label": "來看我！",
              "uri": url
            },
            "flex": 5,
            "position": "relative",
            "margin": "sm",
            "height": "sm",
            "style": "primary",
            "color": "#81C0C0",
            "adjustMode": "shrink-to-fit",
            "offsetTop": "none",
            "offsetBottom": "none",
            "offsetStart": "none"
          },
          {
            "type": "button",
            "action": {
              "type": "message",
              "label": "告訴大家！",
              "text": f"我喜歡這間！！\n\n{title}\n[價格] {price}\n[樓層] {floor}\n[位置] {mrt}\n[網址] {url}"
            },
            "color": "#81C0C0",
            "flex": 5,
            "position": "relative",
            "margin": "sm",
            "height": "sm",
            "style": "primary",
            "adjustMode": "shrink-to-fit",
            "offsetTop": "none",
            "offsetBottom": "none",
            "offsetStart": "none"
          }
        ]
      },
      "styles": {
        "body": {
          "separator": False
        }
      }
    }
    return FlexBubble.from_dict(bubble)

def get_flex_messages(houses):
    num = 0
    bubbles = list()
    with open("visited_houses.txt", "a+") as f:
        for house in houses:
            if num >= 180:
                break

            post_id    = house["post_id"]
            title      = house["title"]
            url        = "https://rent.591.com.tw/home/{}".format(house["post_id"])
            floor      = house["floor_str"]
            price      = house["price"] + " " + house["price_unit"]
            first_img  = "https://s.591.com.tw/build/static/house/rentDetail/images/no-img.png"
            mrt        = ""
            if len(house["photo_list"]) > 0:
                first_img = house["photo_list"][0]
            f.write(str(post_id) + "\n")
            
            if "surrounding" in house and "type" in house["surrounding"]:
                if house["surrounding"]["type"] == "subway_station":
                    mrt = house["surrounding"]["desc"] + house["surrounding"]["distance"]
                    distance = re.match("\d+", house["surrounding"]["distance"])
                    if not distance:
                        continue
                    if int(distance.group(0)) > 1000:
                        continue
                        
            bubbles.append(get_flex_bubble(
                title = title,
                url = url,
                floor = floor,
                price = price,
                first_img = first_img,
                mrt = mrt
            ))

            num += 1

    bs = list()
    messages = list()
    for b in bubbles:
        bs.append(b)
        if len(bs) == 12:
            carousel = FlexCarousel(contents=bs)
            messages.append(FlexMessage(alt_text="今天的看房清單～", contents=carousel))
            bs = list()
        
    if len(bs) > 0:
        carousel = FlexCarousel(contents=bs)
        messages.append(FlexMessage(alt_text="今天的看房清單～", contents=carousel))

    return messages

def send_flex_messages(houses):
    
    messages = get_flex_messages(houses)
    ms = list()
    if len(messages) == 0:
        ms = [TextMessage(text="非常抱歉！\n今天找不到任何合適的房間Q_Q")]
    else:
        ms = list()
        ms.append(TextMessage(text="晚上好！\n這是今天的看房清單!!"))
        for m in messages:
            ms.append(m)
            if len(ms) == 5:
                request = PushMessageRequest(
                    to = group_id,
                    messages = ms
                )
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.push_message(request)
                ms = list()
            
    if len(ms) > 0:
        request = PushMessageRequest(
            to = group_id,
            messages = ms
        )
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(request)

if __name__ == "__main__":
    houses = list()
    for page in range(1, 6):
        for mrt_line in get_mtr_lines():
            for region in get_region():
                filter_params, sort_params = get_params(mrt_line, region)
                hs = search_houses(filter_params, sort_params, page)
                houses.extend(hs)
    
    not_visited_houses = list()
    visited_houses = get_visited_houses()
    
    for house in houses:
        if house["post_id"] not in visited_houses:
            not_visited_houses.append(house)
            visited_houses.append(house["post_id"])

    send_flex_messages(not_visited_houses)
        
