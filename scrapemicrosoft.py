# -*- coding: utf-8 -*-
"""ScrapeMicrosoft_rev1.py

This is a short program to scrape microsoft website and determine if an item is in stock

Rev1-added a daily text to confirm bot is still runnning
    -added a text on errors

Future functionality desired:
 -better error handling
 -alt: check if there's a network connection before attempting to run the script and failing
 -move secrets.py info to environmental variables (lowest priority)
 -incorporate async and await
 Xremove global variables
 Xcalculate delay instead of assuming 600 seconds, calc time to next X min increment 
"""

import json
import re
import secrets
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz
import requests
from bs4 import BeautifulSoup

# constants
UPDATE_INTERVAL = 5  # in minutes


def time_to_send_daily_update(factors: dict):
    if (factors.get("cst_now").hour == 18) and (
        factors.get("cst_now").minute < UPDATE_INTERVAL
    ):
        # factors.update({'daily_update_sent': True})
        return True
    else:
        # if factors.get('cst_now').hour == 0:
        #     factors.update({'daily_update_sent': False})
        return False


def send_notification(content):
    email = secrets.email
    pas = secrets.password

    sms_gateway = secrets.phone_target + "@tmomail.net"
    # The server we use to send emails in our case it will be gmail but every email provider has a different smtp
    # and port is also provided by the email provider.
    smtp = "smtp.gmail.com"
    port = 587
    # This will start our email server
    server = smtplib.SMTP(smtp, port)
    # Starting the server
    server.starttls()
    # Now we need to login
    server.login(email, pas)

    # Now we use the MIME module to structure our message.
    msg = MIMEMultipart()
    msg["From"] = email
    msg["To"] = sms_gateway
    # Make sure you add a new line in the subject
    msg["Subject"] = content[0] + "\n"
    # Make sure you also add new lines to your body
    body = content[1] + "\n"
    # and then attach that body furthermore you can also send html content.
    msg.attach(MIMEText(body, "plain"))

    sms = msg.as_string()

    server.sendmail(email, sms_gateway, sms)

    # lastly quit the server
    server.quit()


def update(factors: dict):
    # send the 10 minute update to screen
    # check if it's time to send the daily text, send if it is
    print("Checked at ", factors.get("cst_now").strftime(r"%m/%d %I:%M %p"))
    if time_to_send_daily_update(factors):
        days_running = (factors.get("cst_now") - factors.get("time_started")).days
        content = (
            "Daily Update",
            f"Botcheck has been running for {days_running} days, still not in stock.",
        )
        send_notification(content)
        if factors.get("daily_failures") > 0:
            content = (
                f"Botcheck has encountered {factors.get('daily_failures')} errors."
            )
            send_notification(content)
            factors.update({"daily_failures": 0})


def check_inventory(factors: dict):
    page_html = get_page_html(factors)
    if check_item_in_stock(page_html, factors):
        send_notification(
            ("In Stock", "Windows Surface Laptop 4 with Ryzen now in stock")
        )
        exit()  # Terminate
    else:
        print("Out of stock still")
    return None


def get_page_html(factors: dict):
    url = "https://www.microsoft.com/en-us/store/configure/Surface-Laptop-4-for-Business/929894RG3GD7?crosssellid=&selectedColor=000000&preview=&previewModes="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    }
    page = requests.get(url, headers=headers)
    # print("status Code", page.status_code)
    if page.status_code != 200:
        factors["daily_failures"] += 1
    return page.content


def is_Ryzen7_and_15in(description, factors: dict):
    good = re.compile(
        r"15.+?AMD Ryzen.+?4980U, 16GB RAM, 512GB SSD.*?",
        flags=re.IGNORECASE | re.DOTALL,
    )
    result = good.search(description)
    if not (type(result) == type(None)):
        # print("Result matching:", result)
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
        # print('as button:', button)
        b_soup = BeautifulSoup(str(button), "html.parser")
        # print('as button soup:', b_soup.button)
        button_dict = b_soup.button.attrs
        # print('as dict:', button_dict)
        button_dict = json.loads(button_dict["data-skuinfo"])
        # print(button_dict)
        for computer in button_dict:
            # print(button_dict[computer])
            heading = button_dict[computer]["Heading"]
            stock = button_dict[computer]["IsOutOfStock"]
            if is_Ryzen7_and_15in(heading, factors):
                result.append(stock)
    # print(bool(sum(result * 1)))
    return bool(sum(result * 1))


def calc_delay(factors: dict) -> float:
    delay = (
        (factors["cst_now"].minute // UPDATE_INTERVAL) * UPDATE_INTERVAL
        + UPDATE_INTERVAL
    ) * 60 - (factors["cst_now"].minute * 60 + factors["cst_now"].second)
    return delay


def main():
    factors = dict()
    factors["time_started"] = pytz.utc.localize(datetime.utcnow()).astimezone(
        pytz.timezone("America/Chicago")
    )
    factors["daily_update_sent"] = False
    factors["daily_failures"] = 0

    while True:
        factors["utc_now"] = pytz.utc.localize(datetime.utcnow())
        factors["cst_now"] = factors["utc_now"].astimezone(
            pytz.timezone("America/Chicago")
        )
        check_inventory(factors)
        update(factors)

        # check how long until next update increment
        delay = calc_delay(factors)
        print(delay)
        time.sleep(delay)  # wait for the delay and try again


if __name__ == "__main__":
    main()
