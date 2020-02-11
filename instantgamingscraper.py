import requests
from bs4 import BeautifulSoup
import logging
import os
from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time

if __package__ is None or __package__ == "":
    from helpers import (
        get_arguments,
        get_config,
        set_interval,
        strip_accents,
        format_string,
    )
    from models import Product
else:
    from .helpers import (
        get_arguments,
        get_config,
        set_interval,
        strip_accents,
        format_string,
    )
    from .models import product

DEFAULT_CONFIG_FILE = os.path.join(".", "config.yml")
AMAZON_TLD = "fr"

AMAZON_BASE_PRODUCT_URL = f"https://www.amazon.{AMAZON_TLD}/dp/"
logger = logging.getLogger(__name__)

DEFAULT_PORT = 587
DEFAULT_SMTP_SERVER = "smtp.gmail.com"

DEFAULT_SLEEP = 3600
DEFAULT_ITERATION_SLEEP = 10

DEFAULT_CREDENTIAL = "credential.json"

headers = {"User-Agent": "Mozilla/5.0"}


class AmazonTracker:
    def __init__(self):
        self.products = []
        self.config_file = DEFAULT_CONFIG_FILE
        self.checked_products = []
        self.sleep = DEFAULT_SLEEP
        self.iteration_sleep = DEFAULT_ITERATION_SLEEP
        self.email_address = ""
        self.password = ""
        self.enable_notification = False
        self.enable_email = False
        self.credential = DEFAULT_CREDENTIAL

    def init_arguments(self):
        arguments = get_arguments(None)

        if arguments.verbose:
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s :: %(levelname)s :: %(module)s :: %(lineno)s :: %(funcName)s :: %(message)s"
            )
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)

            if arguments.verbose == 0:
                logger.setLevel(logging.NOTSET)
            elif arguments.verbose == 1:
                logger.setLevel(logging.DEBUG)
            elif arguments.verbose == 2:
                logger.setLevel(logging.INFO)
            elif arguments.verbose == 3:
                logger.setLevel(logging.WARNING)
            elif arguments.verbose == 4:
                logger.setLevel(logging.ERROR)
            elif arguments.verbose == 5:
                logger.setLevel(logging.CRITICAL)

            logger.addHandler(stream_handler)

        if arguments.email is not None and arguments.password is not None:
            self.email_address = arguments.email
            self.password = arguments.password
            self.enable_email = True

        if arguments.notification is not None:
            self.enable_notification = True
            self.credential = arguments.notification
            cred = credentials.Certificate(self.credential)
            firebase_admin.initialize_app(cred)

        logger.debug("config_file : %s", self.config_file)
        logger.debug("email : %s", self.email_address)
        logger.debug("password : %s", self.password)
        logger.debug("enable_notification : %s", self.enable_notification)
        logger.debug("credential : %s", self.credential)

    def init_config(self):
        config = get_config(self.config_file)

        if "products" in config and config["products"] is not None:
            self.products = config["products"]
        else:
            self.products = []

        if "email" in config and config["email"] is not None:
            self.email = config["email"]
        else:
            self.email = {}

        if "sleep" in config and config["sleep"] is not None:
            self.sleep = float(config["sleep"])

        if "iteration_sleep" in config and config["iteration_sleep"] is not None:
            self.iteration_sleep = float(config["iteration_sleep"])

        logger.debug("products : %s", self.products)
        logger.debug("email : %s", self.email)
        logger.debug("sleep : %s", self.sleep)
        logger.debug("iteration_sleep : %s", self.iteration_sleep)

    def check_products(self):
        self.init_config()

        print("Check products...")

        for product in self.products:
            if product["code"] not in self.checked_products:
                print(f" - {product['code']}")
                self.check_product(product)

            time.sleep(self.iteration_sleep)

    def check_product(self, product):
        logger.debug("product['code'] : %s", product["code"])

        url = f"{AMAZON_BASE_PRODUCT_URL}{product['code']}"

        logger.debug("url : %s", url)

        page = BeautifulSoup(requests.get(url, headers=headers).content, "html.parser")

        tracked_product = Product()
        tracked_product.code = product["code"]
        tracked_product.url = url

        product_title_tag = page.find(id="productTitle")

        if product_title_tag is None:
            logger.debug("spam detected")
            time.sleep(15)  # spam detected
            return

        tracked_product.title = product_title_tag.text.strip()

        if "selector" in product:
            count = (
                product["selector"]["count"] if "count" in product["selector"] else 0
            )
            price_tag = page.select(product["selector"]["value"])[count]
        else:
            price_tag = page.find(id="priceblock_ourprice")

        if price_tag is not None:
            price = price_tag.text.strip()

            tracked_product.price = float(
                price[0 : price.rfind(" ") - 1].replace(",", ".")
            )

            logger.debug("product.title : %s", tracked_product.title)
            logger.debug("product.price : %f", tracked_product.price)

            if "price" in product:
                logger.debug("checked price : %f", product["price"])
                if tracked_product.price <= product["price"]:
                    logger.debug(
                        "price lower (%s) : %f -> %f",
                        product["code"],
                        product["price"],
                        tracked_product.price,
                    )

                    if self.enable_email:
                        subject = format_string(
                            self.email["subject"],
                            tracked_product.title,
                            str(tracked_product.price),
                            url,
                        )
                        body = format_string(
                            self.email["body"],
                            tracked_product.title,
                            str(tracked_product.price),
                            url,
                        )

                        self.send_email(subject=subject, body=body)

                    if self.enable_notification:
                        self.send_notification_topic(
                            "amazon_tracker",
                            tracked_product.title,
                            str(tracked_product.price),
                            url,
                        )

                        if "registration_token" in self.email:
                            for token in email["registration_token"]:
                                self.send_notification_device(
                                    token,
                                    tracked_product.title,
                                    str(tracked_product.price),
                                    url,
                                )

                    # self.checked_products.append(product["code"])
            elif "reduction" in product:
                if (
                    page.find("span", {"class": "priceBlockStrikePriceString"})
                    is not None
                ):
                    print("price reductionin page")
            else:
                logger.debug("produce %s available", product["co"])

                if self.enable_email:
                    self.send_email(
                        product["code"], title=tracked_product.title, url=url
                    )

                if self.enable_notification:
                    self.send_notification_topic(
                        "amazon_tracker", tracked_product.title, "Is available", url
                    )

                # self.checked_products.append(product["code"])

    def send_email(self, subject, body):
        logger.debug("subject : %s", subject)
        logger.debug("body : %s", body)

        message = MIMEMultipart()
        message["From"] = self.email_address
        message["Subject"] = subject
        message.attach(MIMEText(body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(DEFAULT_SMTP_SERVER, DEFAULT_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(self.email_address, self.password)
            server.sendmail(
                "AmazonTracker", self.email["destinations"], message.as_string()
            )
            server.close()

    def send_notification_topic(self, topic="", title="", body="", url=""):
        logger.debug("send_notification")

        topic = "amazon_tracker"

        message = messaging.Message(
            data={"title": title, "body": body, "url": url}, topic=topic,
        )

        response = messaging.send(message)

    def send_notification_device(
        self, registration_token="", title="", body="", url=""
    ):
        message = messaging.Message(
            data={"title": title, "body": body, "url": url}, token=registration_token,
        )

        response = messaging.send(message)

    def run(self):
        set_interval(self.check_products, self.sleep, True)
