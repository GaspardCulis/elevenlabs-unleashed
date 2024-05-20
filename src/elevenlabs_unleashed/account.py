from time import monotonic, sleep
import names
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from random import randint, sample, shuffle
import string
import requests
import re
import os

BASE_URL = "https://beta.elevenlabs.io"
SIGNUP_URL = "https://beta.elevenlabs.io/sign-up"
MAIL_DOMAIN = "txcct.com"


def _generate_email():
    """
    Generate a random email address using names library
    """
    first_name = names.get_first_name()
    last_name = names.get_last_name()
    if randint(0, 1) == 0:
        return f"{first_name}.{last_name}{randint(0, 9999)}@{MAIL_DOMAIN}".lower()
    return f"{first_name}{randint(0, 9999)}@{MAIL_DOMAIN}".lower()


def _generate_password():
    """
    Generate a random password
    """
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    num = string.digits
    symbols = string.punctuation

    temp = sample(upper, randint(1, 2))
    temp += sample(lower, randint(8, 10))
    temp += sample(num, randint(1, 3))
    temp += sample(symbols, 1) + ["#"]

    shuffle(temp)

    return "".join(temp)


def _get_confirmation_link(mail: str):
    """
    Use 1secmail API to get the 11labs confirmation link from the email
    @FIX : if the email has already been used, previous random emails could be used.
    """

    # Get the latest email id
    mail_user = mail.split("@")[0]
    http_get_url = (
        "https://www.1secmail.com/api/v1/?action=getMessages&login="
        + mail_user
        + "&domain="
        + MAIL_DOMAIN
    )

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
    http_get_url_single = (
        "https://www.1secmail.com/api/v1/?action=readMessage&login="
        + mail_user
        + "&domain="
        + MAIL_DOMAIN
        + "&id="
        + str(latest_mail_id)
    )
    mail_content = requests.get(http_get_url_single).json()["textBody"]

    # Parse the email content to get the confirmation link
    url_extract_pattern = "https?:\\/\\/beta[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)"
    urls = re.findall(url_extract_pattern, mail_content)
    if len(urls) > 1:
        raise Exception("Multiple confirmation links found")
    elif len(urls) == 1:
        return urls[0]

    raise Exception("Confirmation link not found")


def create_account():
    """
    Create an account on Elevenlabs and return the email, password and api key
    """
    options = Options()
    options.headless = os.environ.get("DEBUG", "0") == "0"
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1440,1280")
    driver = uc.Chrome(options=options)

    driver.get(SIGNUP_URL)

    email = _generate_email()
    password = _generate_password()

    cookie_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyButtonDecline"))
    )
    cookie_button.click()

    email_input = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.NAME, "email")
    )
    email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(password)

    terms_checkbox = driver.find_element(By.NAME, "terms")
    driver.execute_script("arguments[0].click();", terms_checkbox)

    captcha_iframe = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.XPATH, "//iframe[@tabindex='0']")
    )
    driver.switch_to.frame(captcha_iframe)
    captcha_checkbox = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.ID, "checkbox")
    )
    # Wait for aria-checked to be true
    t0 = monotonic()
    while captcha_checkbox.get_attribute("aria-checked") == "false":
        sleep(0.1)
        if monotonic() - t0 > 20:
            raise Exception("Captcha not checked in time")

    driver.switch_to.default_content()

    sleep(0.5)
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    submit_button.click()

    link = _get_confirmation_link(email)

    driver.get(link)

    close_button = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.XPATH, "//button[text()='Close']")
    )
    close_button.click()

    email_input = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.XPATH, "//input[@type='email']")
    )
    email_input.send_keys(email)

    password_input = driver.find_element(By.XPATH, "//input[@type='password']")
    password_input.send_keys(password)

    sleep(0.5)
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    submit_button.click()

    name_input = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.NAME, "name")
    )
    sleep(0.5)
    name_input.send_keys(email)

    from_list = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(
            By.XPATH, "//button[@aria-haspopup='listbox']"
        )
    )

    from_list.send_keys(Keys.ARROW_DOWN)

    sleep(0.1)
    li_option = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.XPATH, "//li[@role='option']")
    )
    li_option.click()

    next_button = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.CLASS_NAME, "btn-primary")
    )
    next_button.click()

    sleep(0.1)
    containers = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_elements(By.CLASS_NAME, "flex-wrap")
    )

    for i in range(2):
        containers[i].find_element(By.TAG_NAME, "div").click()
        sleep(0.2)

    sleep(0.5)
    stacks = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_elements(By.CLASS_NAME, "stack")
    )

    stacks[-1].find_elements(By.TAG_NAME, "button")[-1].click()

    menu_list = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR, 'div[role="menu"][style*="visibility: visible"]'
        )
    )
    profile_button = menu_list.find_element(By.TAG_NAME, "button")
    profile_button.click()

    api_key_input = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.XPATH, "//input[@type='password']")
    )

    api_key = ""
    while api_key == "":
        api_key = api_key_input.get_attribute("value")
        sleep(0.1)

    driver.quit()

    return email, password, api_key
