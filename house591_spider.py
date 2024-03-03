import time
import random
import requests
from bs4 import BeautifulSoup


    def search(filter_params=None, sort_params=None, want_page=1, max_num=100):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.68",
        }
        total_count = 0
        house_list = []
        page = 0

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

        while page < want_page:
            params += f"&firstRow={page*30}"
            r = s.get(url, params=params, headers=headers)
            if r.status_code != requests.codes.ok:
                print("請求失敗", r.status_code)
                break
            page += 1

            data = r.json()
            total_count = data["records"]
            house_list.extend(data["data"]["data"])
            if len(house_list) >= max_num:
                break
            time.sleep(random.uniform(2, 5))

        return total_count, house_list[:max_num]

if __name__ == "__main__":
    house591_spider = House591Spider()
    mrt = [4178, 4221, 4233, 4234, 66266, 4232, 4231, 4184, 4200, 4233, 66359, 4248, 4245, 4244, 4249, 4189, 4190]
    region = [1, 3]
    wanted_columns = ["title", "post_id", "floor_str", "price", "price_unit", "photo_list", "surrounding"]
    filter_params = {
        "region": "1",
        "mrtcoods": ",".join(list(map(str, mrt))),
        "rentprice": "12000,22000",
        "showMore": "1",
        "multiNotice": "not_cover",
        "other": "near_subway"
    }

    sort_params = {
        "order": "posttime",
        "orderType": "desc"
    }
    
    total_count, houses = house591_spider.search(filter_params, sort_params, want_page=1, max_num=10)
    print("搜尋結果房屋總數：", total_count)
    for house in houses:
        title      = house["title"]
        url        = "https://rent.591.com.tw/home/{}".format(house["post_id"])
        floor      = house["floor_str"]
        price      = house["price"] + " " + house["price_unit"]
        photo_list = house["photo_list"]
        surrounding = ""
        if "surrounding" in house:
            if house["surrounding"]["type"] == "subway_station":
                surrounding = house["surrounding"]["desc"] + " " + house["surrounding"]["distance"]

        output_str = f"\
        [{title}]\n\
        網址: {url}\n\
        價錢: {price}\n\
        樓層: {floor}\n\
        最近捷運站: {surrounding}\n"
        print(output_str)
            
    print(houses[0])
    
    
