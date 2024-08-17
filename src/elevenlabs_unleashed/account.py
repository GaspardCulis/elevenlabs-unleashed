from time import monotonic, sleep
import names
import requests
import undetected_chromedriver as uc
from selenium.common.exceptions import JavascriptException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from random import randint, sample, shuffle
import string
import re
import os


BASE_URL = "https://elevenlabs.io"
SIGNUP_URL = f"{BASE_URL}/app/sign-up"
SIGNIN_URL = f"{BASE_URL}/app/sign-in"
MAIL_DOMAIN = "dpptd.com"


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
    url_extract_pattern = "(https:\/\/elevenlabs\.io\/app\/action\?mode=verifyEmail&oobCode=.*newUser=true)"
    urls = re.findall(url_extract_pattern, mail_content)
    if len(urls) > 1:
        raise Exception("Multiple confirmation links found")
    elif len(urls) == 1:
        return urls[0]

    raise Exception("Confirmation link not found")


class ElevenLabsWebsite:
    def __init__(self, driver: uc.Chrome) -> None:
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.get(BASE_URL)

    def signup(self):
        return _ElevenLabsWebsiteSignup(self.driver)

    def signin(self):
        return _ElevenLabsWebsiteSignin(self.driver)

    def verify_email(self, confirmation_link: str):
        self.driver.get(confirmation_link)
        return self

    def check_cookie_banner(self):
        consent_value = self.driver.execute_script(
            "return localStorage.getItem('ph_consentDecision')"
        )

        if consent_value != "false":
            cookie_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.ID, "CybotCookiebotDialogBodyButtonDecline")
                )
            )
            cookie_button.click()
        return self

    def sleep(self, seconds: float):
        sleep(seconds)
        return self

    def quit(self):
        self.driver.quit()


class _ElevenLabsWebsiteSignup(ElevenLabsWebsite):
    def __init__(self, driver: uc.Chrome) -> None:
        super().__init__(driver)
        self.driver.get(SIGNUP_URL)

    def set_email(self, email: str):
        email_input = self.wait.until(
            lambda driver: driver.find_element(By.XPATH, "//input[@type='email']")
        )
        email_input.send_keys(email)
        return self

    def set_password(self, password: str):
        password_input = self.wait.until(
            lambda driver: driver.find_element(By.XPATH, "//input[@type='password']")
        )
        password_input.send_keys(password)
        return self

    def check_terms(self):
        terms_checkbox = self.wait.until(
            lambda driver: driver.find_element(By.NAME, "terms")
        )
        try:
            self.driver.execute_script(
                "arguments[0].previousSibling.click();", terms_checkbox
            )
        except JavascriptException:
            self.driver.execute_script("arguments[0].checked = true;", terms_checkbox)

        return self

    def submit(self):
        submit_button = self.wait.until(
            lambda driver: driver.find_element(By.TAG_NAME, "form")
        )
        submit_button.submit()
        return super()

    def check_captcha(self):
        try:
            captcha_iframe = self.driver.find_element(
                By.XPATH, "//iframe[@tabindex='0']"
            )

            self.driver.switch_to.frame(captcha_iframe)
            captcha_checkbox = self.wait.until(
                lambda driver: driver.find_element(By.ID, "checkbox")
            )
            # Wait for aria-checked to be true
            t0 = monotonic()
            while captcha_checkbox.get_attribute("aria-checked") == "false":
                sleep(0.1)
                if monotonic() - t0 > 20:
                    raise Exception("Captcha not checked in time")

            self.driver.switch_to.default_content()
        except NoSuchElementException:
            pass

        return self


class _ElevenLabsWebsiteSignin(ElevenLabsWebsite):
    def __init__(self, driver: uc.Chrome) -> None:
        super().__init__(driver)
        self.driver.get(SIGNIN_URL)

    def set_email(self, email: str):
        email_input = self.wait.until(
            lambda driver: driver.find_element(By.XPATH, "//input[@type='email']")
        )
        email_input.send_keys(email)

        return self

    def set_password(self, password: str):
        password_input = self.wait.until(
            lambda driver: driver.find_element(By.XPATH, "//input[@type='password']")
        )
        password_input.send_keys(password)
        return self

    def submit(self):
        submit_button = self.wait.until(
            lambda driver: driver.find_element(By.TAG_NAME, "form")
        )
        submit_button.submit()
        return _ElevenLabsWebsiteOnBoarding(self.driver)


class _ElevenLabsWebsiteOnBoarding(ElevenLabsWebsite):
    def __init__(self, driver: uc.Chrome) -> None:
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def skip(self):
        skip_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Skip"]'))
        )
        skip_button.click()
        return _ElevenLabsWebsiteDashboard(self.driver)


class _ElevenLabsWebsiteDashboard(ElevenLabsWebsite):
    def __init__(self, driver: uc.Chrome) -> None:
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def account_menu(self):
        account_button = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Your profile']")
            )
        )
        self.driver.execute_script("arguments[0].click();", account_button)
        return self

    def profile_and_api_key(self):
        profile_button = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@aria-label='Profile + API key']")
            )
        )
        profile_button.click()
        return self

    def refresh_api_key(self):
        refresh_api_button = self.wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "/html/body/div[3]/div/div/div/div[2]/div/div/div/div[2]/div[1]/div[2]/div/button[2]",
                )
            )
        )
        refresh_api_button.click()

        confirm_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button[text()="Confirm"]'))
        )
        confirm_button.click()
        return self

    def get_api_key(self):
        api_key_input = self.wait.until(
            lambda driver: driver.find_element(
                By.XPATH, '//input[@aria-label="API Key"]'
            )
        )
        api_key = ""
        while api_key == "":
            api_key = api_key_input.get_attribute("value")
            sleep(0.1)
        return api_key


def create_account():
    """
    Create an account on Elevenlabs and return the email, password and api key
    """
    options = Options()
    options.headless = os.environ.get("DEBUG", "0") == "0"
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1440,1280")

    email = _generate_email()
    password = _generate_password()

    labs = ElevenLabsWebsite(uc.Chrome(options=options))
    api_key = (
        labs.check_cookie_banner()
        .signup()
        .set_email(email)
        .set_password(password)
        .check_terms()
        .sleep(0.5)
        .check_captcha()
        .submit()
        .verify_email(_get_confirmation_link(email))
        .signin()
        .set_email(email)
        .set_password(password)
        .sleep(0.5)
        .submit()
        .skip()
        .account_menu()
        .profile_and_api_key()
        .refresh_api_key()
        .get_api_key()
    )

    labs.quit()

    return email, password, api_key
