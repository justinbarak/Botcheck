# -*- coding: utf-8 -*-
"""scrape_bike.py

This is a short program to scrape the gopowerbike website and determine if an item is in stock

"""

import time
from datetime import datetime, timedelta
from send_text import send_text
import scrapemicrosoft as template
import secrets

import pytz
import requests
from bs4 import BeautifulSoup

# constants
UPDATE_INTERVAL = 5  # in minutes
NOTIFICATION_NAME = "GoPowerBike Battery"


def update(factors: dict):
    # send the UPDATE_INTERVAL minute update to screen
    # check if it's time to send the daily text, send if it is
    print("Checked at ", factors.get("cst_now").strftime(r"%m/%d %I:%M %p"))
    if template.time_to_send_daily_update(factors):
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
            content = f"{NOTIFICATION_NAME} Botcheck has encountered {factors.get('daily_failures')} errors."
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
            send_text(
                ("In Stock", "Gopowerbike Battery is now in stock"),
                secrets.phone_target2,
            )
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
    global daily_failures
    url = "https://gopowerbike.com/collections/batteries/products/battery-1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    }
    page = requests.get(url, headers=headers)
    if page.status_code != 200:
        raise RuntimeError(f"While looking up html, page result was {page.status_code}")
    return page.content


def check_item_in_stock(page_html, factors: dict):
    soup = BeautifulSoup(page_html, "html.parser")
    buttons = soup.findAll("button", {"id": "AddToCart-product-template"})
    # "id": "AddToCart-product-template"
    for button in buttons:
        b_soup = BeautifulSoup(str(button), "html.parser")
        button_dict = b_soup.button.attrs
        button_dict = button_dict.get("disabled", "")
        if button_dict != "disabled":
            return True
    return False


def main():
    factors = dict()
    factors["time_started"] = pytz.utc.localize(datetime.utcnow()).astimezone(
        pytz.timezone("America/Chicago")
    )
    factors["daily_failures"] = 0

    # as requested by client send initialization text
    # send_text(
    #     (
    #         "Botcheck Running",
    #         "You will be notified when Gopowerbike Battery is back in stock.",
    #     ),
    #     secrets.phone_target2,
    # )

    while True:
        template.update_time(factors)
        check_inventory(factors)
        update(factors)

        # check how long until next update increment
        delay = template.calc_delay(factors)
        # print(delay)
        time.sleep(delay)  # wait for the delay and try again


if __name__ == "__main__":
    main()
