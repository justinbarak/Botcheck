# -*- coding: utf-8 -*-
"""scrape_antenna.py


"""

import time
from datetime import datetime, timedelta
from send_text import send_text
import scrapemicrosoft as template
import secrets

import pytz
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.utils import ChromeType
from selenium.webdriver.chrome.options import Options
import logging

# from selenium.webdriver.remote.remote_connection import LOGGER

# constants
UPDATE_INTERVAL = 4  # in minutes
NOTIFICATION_NAME = "McGill 9dBi Antenna"


def update(factors: dict):
    # send the UPDATE_INTERVAL minute update to screen
    # check if it's time to send the daily text, send if it is
    print("Checked at ", factors.get("cst_now").strftime(r"%m/%d %I:%M %p"))
    if template.time_to_send_daily_update(factors):
        days_running = (factors.get("cst_now") - factors.get("time_started")).days
        content = (
            "Daily Update",
            f"Antenna-check has been running for {days_running} days, still not in"
            " stock.",
        )
        try:
            send_text(content)
        except:
            print(f"There was an error sending this text: {content}")
        if factors.get("daily_failures") > 0:
            content = (
                f"{NOTIFICATION_NAME} Botcheck has encountered"
                f" {factors.get('daily_failures')} errors."
            )
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
                ("In Stock", f"{NOTIFICATION_NAME} is now in stock"),
                secrets.phone_target2,
            )
            send_text(
                ("In Stock", f"{NOTIFICATION_NAME} is now in stock"),
                secrets.phone_target,
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
    url = (
        "https://fiz-tech.net/products/9-dbi-tuned-antenna-us-915?variant=41669770608893"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like"
            " Gecko) Chrome/83.0.4103.116 Safari/537.36"
        )
    }
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    driver = webdriver.Chrome(
        ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(),
        options=chrome_options,
    )
    driver.get(url)
    time.sleep(5)
    try:
        page = driver.page_source
        driver.close()
        return page
    except:
        raise RuntimeError(f"While looking up html, an error was encountered.")


def check_item_in_stock(page_html, factors: dict):
    soup = BeautifulSoup(page_html, "html.parser")
    spans = soup.findAll("span", {"id": "AddToCartText"})
    if len(spans) != 1:
        raise RuntimeError(f"{NOTIFICATION_NAME} could not find AddToCartText button")
    if "Sold Out" in spans[0]:
        return False
    return True


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
