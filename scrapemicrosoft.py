# -*- coding: utf-8 -*-
"""scrapemicrosoft.py

This is a short program to scrape microsoft website and determine if an item is in stock

Future functionality desired:
 -tell if client has been text about an item initially, not doing it again, maybe pickle? json?
 -move secrets.py info to environmental variables (lowest priority)
 """

import json
import re
import time
from datetime import datetime, timedelta
from send_text import send_text

import pytz
import requests
from bs4 import BeautifulSoup

# constants
UPDATE_INTERVAL = 5  # in minutes
NOTIFICATION_NAME = "Ryzen Laptop"


def time_to_send_daily_update(factors: dict):
    if (factors.get("cst_now").hour == 18) and (
        factors.get("cst_now").minute < UPDATE_INTERVAL
    ):
        return True
    else:
        return False


def update(factors: dict):
    # send the UPDATE_INTERVAL minute update to screen
    # check if it's time to send the daily text, send if it is
    print("Checked at ", factors.get("cst_now").strftime(r"%m/%d %I:%M %p"))
    if time_to_send_daily_update(factors):
        days_running = (factors.get("cst_now") - factors.get("time_started")).days
        content = (
            "Daily Update",
            f"Microsoft Botcheck has been running for {days_running} days, still not in stock.",
        )
        try:
            send_text(content)
        except:
            print(f"There was an error sending this text: {content}")
        if factors.get("daily_failures") > 0:
            content = f"Microsoft Botcheck has encountered {factors.get('daily_failures')} errors."
            try:
                send_text(content)
            except:
                print(f"There was an error sending this text: {content}")
            factors.update({"daily_failures": 0})
    return None


def check_inventory(factors: dict):
    try:
        page_html = get_page_html(factors)
        if check_item_in_stock(page_html, factors):
            send_text(("In Stock", "Windows Surface Laptop 4 with Ryzen now in stock"))
            exit()  # Terminate
        else:
            print(f"{NOTIFICATION_NAME} Out of stock still")
    except Exception as error:
        print(
            f"{NOTIFICATION_NAME}\n",
            f"There was an error in checking for {NOTIFICATION_NAME} at ",
            f'{factors.get("cst_now").strftime(r"%m/%d %I:%M %p")}.\n',
            error.args,
        )
        factors["daily_failures"] += 1
    return None


def get_page_html(factors: dict):
    url = "https://www.microsoft.com/en-us/store/configure/Surface-Laptop-4-for-Business/929894RG3GD7?crosssellid=&selectedColor=000000&preview=&previewModes="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    }
    page = requests.get(url, headers=headers)
    if page.status_code != 200:
        raise RuntimeError(f"While looking up html, page result was {page.status_code}")
    return page.content


def is_Ryzen7_and_15in(description: str, factors: dict):
    good = re.compile(
        r"15.+?AMD Ryzen.+?4980U, 16GB RAM, 512GB SSD.*?",
        flags=re.IGNORECASE | re.DOTALL,
    )
    result = good.search(description)
    print(description, result)
    if not (type(result) == type(None)):
        print("Result matching:", result)
        if result == None:
            factors["daily_failures"] += 1
        return True
    else:
        return False


def check_item_in_stock(page_html, factors: dict):
    soup = BeautifulSoup(page_html, "html.parser")
    buttons = soup.findAll("button", {"data-pid": "929894RG3GD7"})
    # "Heading": "15\", Matte Black (Metal), AMD Ryzen™ 7 4980U, 16GB RAM, 512GB SSD"
    # "IsOutOfStock": true
    # "data-pid": "929894RG3GD7"
    # print('How many buttons total?', len(buttons))
    result = list()
    for button in buttons:
        b_soup = BeautifulSoup(str(button), "html.parser")
        button_dict = b_soup.button.attrs
        button_dict = json.loads(button_dict["data-skuinfo"])
        for computer in button_dict:
            heading = button_dict[computer]["Heading"]
            stock = button_dict[computer]["IsOutOfStock"]
            # print(heading, stock)
            if is_Ryzen7_and_15in(heading, factors):
                result.append(not (bool(stock)))
    print(result)
    return bool(sum(result * 1))


def calc_delay(factors: dict) -> float:
    update_time(factors)
    delay = (
        (factors["cst_now"].minute // UPDATE_INTERVAL) * UPDATE_INTERVAL
        + UPDATE_INTERVAL
    ) * 60 - (factors["cst_now"].minute * 60 + factors["cst_now"].second)
    return delay


def update_time(factors: dict):
    factors["utc_now"] = pytz.utc.localize(datetime.utcnow())
    factors["cst_now"] = factors["utc_now"].astimezone(pytz.timezone("America/Chicago"))
    return None


def main():
    factors = dict()
    factors["time_started"] = pytz.utc.localize(datetime.utcnow()).astimezone(
        pytz.timezone("America/Chicago")
    )
    factors["daily_failures"] = 0

    while True:
        update_time(factors)
        check_inventory(factors)
        update(factors)

        # check how long until next update increment
        delay = calc_delay(factors)
        # print(delay)
        time.sleep(delay)  # wait for the delay and try again


if __name__ == "__main__":
    main()
