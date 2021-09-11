# -*- coding: utf-8 -*-
"""scrape_bike.py

This is a short program to scrape the gopowerbike website and determine if an item is in stock

Future functionality desired:
 -tell if client has been text about an item initially, not doing it again, maybe pickle? json?
 -better error handling
 -alt: check if there's a network connection before attempting to run the script and failing
 -move secrets.py info to environmental variables
"""

import secrets
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytz
import requests
from bs4 import BeautifulSoup


def time_to_send_daily_update():
    global daily_update_sent

    if (cst_now.hour == 18) and (daily_update_sent == False):
        daily_update_sent = True
        return True
    else:
        if cst_now.hour == 0:
            daily_update_sent = False

        return False


def send_notification(content, target=secrets.phone_target):
    email = secrets.email
    pas = secrets.password

    sms_gateway = target + "@tmomail.net"
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


def update():
    global daily_failures
    # send the 10 minute update to screen
    # check if it's time to send the daily text, send if it is
    print("Checked at ", cst_now.strftime(r"%m/%d %I:%M %p"))
    if time_to_send_daily_update():
        days_running = (cst_now - time_started).days
        content = (
            "Daily Update",
            f"Botcheck for Bike Battery has been running for {days_running} days, still not in stock.",
        )
        send_notification(content)
        if daily_failures > 0:
            content = f"Botcheck has encountered {daily_failures} errors."
            send_notification(content)
            daily_failures = 0


def check_inventory():
    page_html = get_page_html()
    if check_item_in_stock(page_html):
        send_notification(
            ("In Stock", "Gopowerbike Battery is now in stock"), secrets.phone_target2
        )
        exit()  # Terminate
    else:
        print("Out of stock still")
    return None


def get_page_html():
    global daily_failures
    url = "https://gopowerbike.com/collections/batteries/products/battery-1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    }
    page = requests.get(url, headers=headers)
    # print("status Code", page.status_code)
    if page.status_code != 200:
        daily_failures += 1
    return page.content


def check_item_in_stock(page_html):
    soup = BeautifulSoup(page_html, "html.parser")
    buttons = soup.findAll("button", {"id": "AddToCart-product-template"})
    # "id": "AddToCart-product-template"
    for button in buttons:
        # print('as button:', button)
        b_soup = BeautifulSoup(str(button), "html.parser")
        # print('as button soup:', b_soup.button)
        button_dict = b_soup.button.attrs
        # print('as dict:', button_dict)
        button_dict = button_dict.get("disabled", "")
        # print(button_dict)
        if button_dict != "disabled":
            return True
    # print(bool(sum(result * 1)))
    return False


def main():
    global time_started
    global daily_update_sent
    global daily_failures
    daily_update_sent = False
    time_started = pytz.utc.localize(datetime.utcnow()).astimezone(
        pytz.timezone("America/Chicago")
    )
    daily_failures = 0

    # as requested by client send initialization text
    # send_notification(
    #     (
    #         "Botcheck Running",
    #         "You will be notified when Gopowerbike Battery is back in stock.",
    #     ),
    #     secrets.phone_target2,
    # )

    while True:
        global utc_now
        global cst_now
        try:
            utc_now = pytz.utc.localize(datetime.utcnow())
            cst_now = utc_now.astimezone(pytz.timezone("America/Chicago"))
            check_inventory()
            update()
        # attempt to notify me if/when something breaks
        except Exception as inst:
            print(inst.args)
            send_notification(
                (
                    "Gopowerbike Battery Error",
                    str(inst.args),
                ),
                secrets.phone_target,
            )
        time.sleep(600)  # wait 10 min and try again


if __name__ == "__main__":
    main()
