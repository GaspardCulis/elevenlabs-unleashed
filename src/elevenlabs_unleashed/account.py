from time import monotonic, sleep
import names
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import tempfile
from selenium.webdriver.support.wait import WebDriverWait
from random import randint
import requests
import re
import os

BASE_URL = "https://beta.elevenlabs.io"
SIGNUP_URL = "https://beta.elevenlabs.io/sign-up"
MAIL_DOMAIN = "txcct.com"

HEKT_EXT_PATH = os.path.join(tempfile.gettempdir(), "hektCaptcha-extension.crx")


def _generate_email():
    """
    Generate a random email address using names library
    """
    first_name = names.get_first_name()
    last_name = names.get_last_name()
    if randint(0, 1) == 0:
        return f"{first_name}.{last_name}{randint(0, 99)}@{MAIL_DOMAIN}".lower()
    return f"{first_name}{randint(0, 99)}@{MAIL_DOMAIN}".lower()


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


def __get_latest_hektCaptcha_ext(save_path: str):
    print("Downloading the latest hektCaptcha-extension from Github...")

    url = "https://api.github.com/repos/Wikidepia/hektCaptcha-extension/releases/latest"

    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()

        i = 0
        while (
            i < len(data)
            and data["assets"][i]["content_type"] != "application/x-chrome-extension"
        ):
            i += 1

        if i == len(data):
            raise Exception(
                "Couldn't get the chrome extension asset from the latest hektCaptcha-extension Github release"
            )

        dl_url = data["assets"][i]["browser_download_url"]

        r = requests.get(dl_url)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)
        else:
            raise Exception(
                "Couldn't download the latest hektCaptcha-extension from Github"
            )

    else:
        raise Exception("Couldn't get the latest hektCaptcha-extension Github release")

    print("hektCaptcha-extension downloaded to " + save_path)


def create_account():
    """
    Create an account on Elevenlabs and return the email, password and api key
    """
    if not os.path.exists(HEKT_EXT_PATH):
        __get_latest_hektCaptcha_ext(HEKT_EXT_PATH)
    options = Options()
    options.headless = os.environ.get("DEBUG", "0") == "0"
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1440,1280")
    options.add_extension(HEKT_EXT_PATH)
    driver = webdriver.Chrome(options=options)

    driver.get(SIGNUP_URL)

    email = _generate_email()
    password = _generate_password()

    # cookie_button = WebDriverWait(driver, 10).until(lambda driver: driver.find_element(By.ID, "CybotCookiebotDialogBodyButtonAccept"))
    # cookie_button.click()

    email_input = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(By.NAME, "email")
    )
    email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(password)

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

    account_button = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(
            By.XPATH, "//button[@data-testid='user-menu-button']"
        )
    )
    account_button.click()

    menu_items_container = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element(
            By.XPATH, "//div[starts-with(@id, 'headlessui-menu-items')]"
        )
    )
    id = "headlessui-menu-item-P0-" + str(
        int(menu_items_container.get_attribute("id").split("-")[-1]) + 1
    )
    profile_button = menu_items_container.find_element(By.ID, id)
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
