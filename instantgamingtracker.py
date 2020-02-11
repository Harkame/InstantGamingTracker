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
import cloudscraper
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

if __package__ is None or __package__ == "":
    from helpers import (
        get_arguments,
        get_config,
        set_interval,
        strip_accents,
        format_string,
    )
    from models import game
else:
    from .helpers import (
        get_arguments,
        get_config,
        set_interval,
        strip_accents,
        format_string,
    )
    from .models import game

DEFAULT_CONFIG_FILE = os.path.join(".", "config.yml")
AMAZON_TLD = "fr"

AMAZON_BASE_game_URL = f"https://www.amazon.{AMAZON_TLD}/dp/"
logger = logging.getLogger(__name__)

DEFAULT_PORT = 587
DEFAULT_SMTP_SERVER = "smtp.gmail.com"

DEFAULT_SLEEP = 3600
DEFAULT_ITERATION_SLEEP = 10

DEFAULT_CREDENTIAL = "credential.json"

headers = {"User-Agent": "Mozilla/5.0"}


class InstantGamingTracker:
    def __init__(self):
        self.games = []
        self.config_file = DEFAULT_CONFIG_FILE
        self.checked_games = []
        self.sleep = DEFAULT_SLEEP
        self.iteration_sleep = DEFAULT_ITERATION_SLEEP
        self.email_address = ""
        self.password = ""
        self.enable_notification = False
        self.enable_email = False
        self.credential = DEFAULT_CREDENTIAL

        self.scraper = cloudscraper.create_scraper()

        #self.driver = webdriver.Chrome()

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

        if "games" in config and config["games"] is not None:
            self.games = config["games"]
        else:
            self.games = []

        if "email" in config and config["email"] is not None:
            self.email = config["email"]
        else:
            self.email = {}

        if "sleep" in config and config["sleep"] is not None:
            self.sleep = float(config["sleep"])

        if "iteration_sleep" in config and config["iteration_sleep"] is not None:
            self.iteration_sleep = float(config["iteration_sleep"])

        logger.debug("games : %s", self.games)
        logger.debug("email : %s", self.email)
        logger.debug("sleep : %s", self.sleep)
        logger.debug("iteration_sleep : %s", self.iteration_sleep)

    def check_games(self):
        self.init_config()

        print("Check games...")

        for game in self.games:
            print(game)
            self.check_game(game)

            time.sleep(self.iteration_sleep)

    def check_game(self, game_url):
        logger.debug("game_url : %s", game_url)

        page = BeautifulSoup(requests.get(game_url, headers=headers).content, "html.parser")

        #self.driver.get(game_url)

        #self.driver.get(game_url)

        #time.sleep(5)

        #self.driver.find_element_by_css_selector(".recaptcha-checkbox-border").click()

        # WebDriverWait(self.driver, 5).until(element_present)

        # element.click()

        """
        page = BeautifulSoup(
            self.driver.get(game_url, headers=headers).content, "html.parser"
        )

        """


        title = page.select(".title h1")[0].text
        price = page.find("div", {"class": "price"}).text[:-1]
        discount = page.find("div", {"class": "discount"}).text[:-1]
        platform = page.find("a", {"class": "platform"}).text
        languages = (
            page.find("div", {"class": "languages"})
            .text.replace("Languages", "")
            .strip()
        )  # TODO check if no better solution
        description = page.find("div", {"class": "description"}).text
        release = page.find("div", {"class": "release"}).find("span").text
        rate = page.find("span", {"class": "rate"}).text
        retail_price = page.select(".retail span")[0].text.strip()[:-1]

        logger.debug("title : %s", title)
        logger.debug("price : %s", price)
        logger.debug("discount : %s", discount)
        logger.debug("platform : %s", platform)
        logger.debug("languages : %s", languages)
        # logger.debug("description : %s", description)
        logger.debug("platform : %s", release)
        logger.debug("rate : %s", rate)
        logger.debug("retail_price : %s", retail_price)

        return

        tracked_game.title = game_title_tag.text.strip()

        if "selector" in game:
            count = game["selector"]["count"] if "count" in game["selector"] else 0
            price_tag = page.select(game["selector"]["value"])[count]
        else:
            price_tag = page.find(id="priceblock_ourprice")

        if price_tag is not None:
            price = price_tag.text.strip()

            tracked_game.price = float(
                price[0 : price.rfind(" ") - 1].replace(",", ".")
            )

            logger.debug("game.title : %s", tracked_game.title)
            logger.debug("game.price : %f", tracked_game.price)

            if "price" in game:
                logger.debug("checked price : %f", game["price"])
                if tracked_game.price <= game["price"]:
                    logger.debug(
                        "price lower (%s) : %f -> %f",
                        game["code"],
                        game["price"],
                        tracked_game.price,
                    )

                    if self.enable_email:
                        subject = format_string(
                            self.email["subject"],
                            tracked_game.title,
                            str(tracked_game.price),
                            url,
                        )
                        body = format_string(
                            self.email["body"],
                            tracked_game.title,
                            str(tracked_game.price),
                            url,
                        )

                        self.send_email(subject=subject, body=body)

                    if self.enable_notification:
                        self.send_notification_topic(
                            "amazon_tracker",
                            tracked_game.title,
                            str(tracked_game.price),
                            url,
                        )

                        if "registration_token" in self.email:
                            for token in email["registration_token"]:
                                self.send_notification_device(
                                    token,
                                    tracked_game.title,
                                    str(tracked_game.price),
                                    url,
                                )

                    # self.checked_games.append(game["code"])
            elif "reduction" in game:
                if (
                    page.find("span", {"class": "priceBlockStrikePriceString"})
                    is not None
                ):
                    print("price reductionin page")
            else:
                logger.debug("produce %s available", game["co"])

                if self.enable_email:
                    self.send_email(game["code"], title=tracked_game.title, url=url)

                if self.enable_notification:
                    self.send_notification_topic(
                        "amazon_tracker", tracked_game.title, "Is available", url
                    )

                # self.checked_games.append(game["code"])

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
        set_interval(self.check_games, self.sleep, True)
