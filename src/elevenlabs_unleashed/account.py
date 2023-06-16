from time import monotonic, sleep
import names
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from random import randint
import requests

BASE_URL = "https://beta.elevenlabs.io"
SIGNUP_URL = "https://beta.elevenlabs.io/sign-up"
MAIL_DOMAIN = "icznn.com"

def _generate_email():
    """
    Generate a random email address using names library
    """
    first_name = names.get_first_name()
    last_name = names.get_last_name()
    if  randint(0, 1) == 0:
        return f'{first_name}.{last_name}{randint(0, 99)}@{MAIL_DOMAIN}'.lower()
    return f'{first_name}{randint(0, 99)}@{MAIL_DOMAIN}'.lower()

def _generate_password():
    """
    Generate a random password
    """
    password = ""
    for i in range(0, 12):
        password += chr(randint(97, 122))
    return password

def _get_confirmation_link(mail: str):
    """
    Use 1secmail API to get the 11labs confirmation link from the email
    @FIX : if the email has already been used, previous random emails could be used.
    """

    # Get the latest email id
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

    # Get the email content
    http_get_url_single = "https://www.1secmail.com/api/v1/?action=readMessage&login=" + \
        mail_user+"&domain="+MAIL_DOMAIN+"&id="+str(latest_mail_id)
    mail_content = requests.get(http_get_url_single).json()['textBody']
    
    # Parse the email content to get the confirmation link
    for line in mail_content.split('\n'):
        if line.startswith("https://"):
            return line
        
    raise Exception("Confirmation link not found")

def create_account():
    """
    Create an account on Elevenlabs and return the email, password and api key
    """
    options = Options()
    options.headless = True
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1440,1280")
    driver = webdriver.Chrome(options=options)

    driver.get(SIGNUP_URL)

    email = _generate_email()
    password = _generate_password()

    cookie_button = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonAccept"))
    cookie_button.click()

    email_input = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.NAME, "email"))
    email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(password)

    tos_checkbox =  driver.find_element(By.NAME, "terms")
    tos_checkbox.click()

    sleep(0.5)
    submit_button =  driver.find_element(By.XPATH, "//button[@type='submit']")
    submit_button.click()

    link = _get_confirmation_link(email)

    driver.get(link)
    sleep(2)
    
    driver.get(BASE_URL)

    sign_in_form_button = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.XPATH, "//a[@data-testid='sign-in-button']"))
    sign_in_form_button.click()

    email_input = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.XPATH, "//input[@type='email']"))
    email_input.send_keys(email)

    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    password_input.send_keys(password)

    sleep(0.5)
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    submit_button.click()

    account_button = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.XPATH, "//button[@data-testid='user-menu-button']"))
    account_button.click()

    profile_button = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.XPATH, "//a[starts-with(@id, 'headlessui-menu-item')]"))
    profile_button.click()
    
    api_key_input = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.XPATH, "//input[@type='password']"))
    
    api_key = ''
    while api_key == '':
        api_key = api_key_input.get_attribute("value")
        sleep(0.1)

    driver.quit()

    return email, password, api_key