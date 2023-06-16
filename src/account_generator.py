from time import monotonic, sleep
import names
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from random import randint
import requests

BASE_URL = "https://beta.elevenlabs.io/sign-up"
MAIL_DOMAIN = "icznn.com"

def generate_email():
    first_name = names.get_first_name()
    last_name = names.get_last_name()
    mode = randint(0, 2)
    if mode == 0:
        return f'{first_name}.{last_name}{randint(0, 99)}@{MAIL_DOMAIN}'.lower()
    elif mode == 1:
        return f'{first_name}.{last_name.lower()}@{MAIL_DOMAIN}'
    else:
        return f'{first_name}{randint(0, 99)}@{MAIL_DOMAIN}'.lower()

def generate_password():
    password = ""
    for i in range(0, 12):
        password += chr(randint(97, 122))
    return password

def get_confirmation_link(mail: str):
    mail_user = mail.split('@')[0]
    http_get_url = "https://www.1secmail.com/api/v1/?action=getMessages&login=" + \
        mail_user+"&domain="+MAIL_DOMAIN
    
    latest_mail_id = None
    t0 = monotonic()
    while not latest_mail_id:
        response = requests.get(http_get_url).json()
        if len(response) > 0:
            latest_mail_id = response[0]["id"]
        else:
            sleep(1)
            if monotonic() - t0 > 60:
                raise Exception("Email not received in time")

    http_get_url_single = "https://www.1secmail.com/api/v1/?action=readMessage&login=" + \
        mail_user+"&domain="+MAIL_DOMAIN+"&id="+str(latest_mail_id)
    mail_content = requests.get(http_get_url_single).json()['textBody']
    
    for line in mail_content.split('\n'):
        if line.startswith("https://"):
            return line
        
    raise Exception("Confirmation link not found")

def create_account():
    options = Options()
    #options.headless = True
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    action = ActionChains(driver)
    driver.get(BASE_URL)

    sleep(0.5)

    email = generate_email()
    password = generate_password()

    cookie_button = driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonAccept")
    if cookie_button:
        cookie_button.click()

    email_input = driver.find_element(By.NAME, "email")
    if not email_input:
        raise Exception("Email input not found")
    email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, "password")
    if not password_input:
        raise Exception("Password input not found")
    password_input.send_keys(password)

    tos_checkbox = driver.find_element(By.NAME, "terms")
    if not tos_checkbox:
        raise Exception("TOS checkbox not found")
    tos_checkbox.click()

    sleep(1)
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    if not submit_button:
        raise Exception("Submit button not found")
    submit_button.click()
    sleep(10)

    link = get_confirmation_link(email)

    driver.get(link)
    sleep(1)
    driver.close()

    return email, password

create_account()