# -*- coding: utf-8 -*-
"""ScrapeMicrosoft_rev1.py

This is a short program to scrape microsoft website and determine if an item is in stock

Rev1-added a daily text to confirm bot is still runnning
    -added a text on errors
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import smtplib 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime, timedelta
import pytz
import secrets


def time_to_send_daily_update():
    global daily_update_sent
    
    if (cst_now.hour == 18) and (daily_update_sent==False):
        daily_update_sent = True
        return True
    else:
        if cst_now.hour == 0:
            daily_update_sent = False

        return False

def send_notification(content):
    email = secrets.email
    pas = secrets.password

    sms_gateway = '6308180119@tmomail.net'
    # The server we use to send emails in our case it will be gmail but every email provider has a different smtp 
    # and port is also provided by the email provider.
    smtp = "smtp.gmail.com" 
    port = 587
    # This will start our email server
    server = smtplib.SMTP(smtp,port)
    # Starting the server
    server.starttls()
    # Now we need to login
    server.login(email,pas)

    # Now we use the MIME module to structure our message.
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = sms_gateway
    # Make sure you add a new line in the subject
    msg['Subject'] = content[0] + "\n"
    # Make sure you also add new lines to your body
    body = content[1] + "\n"
    # and then attach that body furthermore you can also send html content.
    msg.attach(MIMEText(body, 'plain'))

    sms = msg.as_string()

    server.sendmail(email,sms_gateway,sms)

    # lastly quit the server
    server.quit()

def update():
    global daily_failures
    # send the 10 minute update to screen
    # check if it's time to send the daily text, send if it is
    print('Checked at ', cst_now.strftime(r'%m/%d %I:%M %p'))
    if time_to_send_daily_update():
        days_running = (cst_now - time_started).days
        content = ('Daily Update',f'Botcheck has been running for {days_running} days, still not in stock.')
        send_notification(content)
        if daily_failures > 0:
            content = f'Botcheck has encountered {daily_failures} errors.'
            send_notification(content)
            daily_failures = 0

def check_inventory():
    page_html = get_page_html()
    if check_item_in_stock(page_html):
        send_notification(('In Stock', 'Windows Surface Laptop 4 with Ryzen now in stock'))
        exit()  # Terminate
    else:
        print("Out of stock still")
    return None

def get_page_html():
    global daily_failures
    url = 'https://www.microsoft.com/en-us/store/configure/Surface-Laptop-4-for-Business/929894RG3GD7?crosssellid=&selectedColor=000000&preview=&previewModes='
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
    page = requests.get(url, headers=headers)
    # print("status Code", page.status_code)
    if page.status_code != 200:
        daily_failures += 1
    return page.content

def is_Ryzen7_and_15in(description):
    global daily_failures
    good = re.compile(r'15.+?AMD Ryzen.+?4980U, 16GB RAM, 512GB SSD.*?', flags=re.IGNORECASE | re.DOTALL)
    result = good.search(description)
    if not (type(result) == type(None)):
        # print("Result matching:", result)
        if result == None:
            daily_failures += 1
        return True
    else:
        return False

def check_item_in_stock(page_html):
    soup = BeautifulSoup(page_html, 'html.parser')
    buttons = soup.findAll("button", {"data-pid": "929894RG3GD7"})
    # "Heading": "15\", Matte Black (Metal), AMD Ryzen™ 7 4980U, 16GB RAM, 512GB SSD"
    # "IsOutOfStock": true
    # "data-pid": "929894RG3GD7"
    # print('How many buttons total?', len(buttons))
    result = list()
    for button in buttons:
        # print('as button:', button)
        b_soup = BeautifulSoup(str(button), 'html.parser')
        # print('as button soup:', b_soup.button)
        button_dict = b_soup.button.attrs
        # print('as dict:', button_dict)
        button_dict = json.loads(button_dict['data-skuinfo'])
        # print(button_dict)
        for computer in button_dict:
            # print(button_dict[computer])
            heading = button_dict[computer]['Heading']
            stock = button_dict[computer]['IsOutOfStock']
            if is_Ryzen7_and_15in(heading):
                result.append(stock)
    # print(bool(sum(result * 1)))
    return bool(sum(result * 1))

def main():
    global time_started
    global daily_update_sent
    global daily_failures
    daily_update_sent = False
    time_started = pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone("America/Chicago"))
    daily_failures = 0

    while True:
        global utc_now
        global cst_now
        

        utc_now = pytz.utc.localize(datetime.utcnow())
        cst_now = utc_now.astimezone(pytz.timezone("America/Chicago"))
        check_inventory()
        update()

        time.sleep(600) # wait 10 min and try again

if __name__=='__main__':
    main()

