#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Pixiv Class
Author: K4YT3X
Date Created: Feb 24, 2018
Last Modified: October 24, 2019

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt

(C) 2018-2019 K4YT3X
"""

# local imports
from illustration import Illustration

# built-in imports
import contextlib
import requests
import selenium
import time
import traceback

# third-party imports
from avalon_framework import Avalon
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains


class Pixiv:
    """Pixiv wrapper

    This class controls the interactions with pixiv.net
    """

    def __init__(self, pixiv_username, pixiv_password):
        self.username = pixiv_username
        self.password = pixiv_password
        self.pixiv = "https://www.pixiv.net"
        self.session = requests.Session()
        self.login(pixiv_username, pixiv_password)
        self.driver = None

    def login(self, username, password):
        """Login into Pixiv

        Use request to send POST request to login into Pixiv
        Cookies are saved into a requests session object
        """
        Avalon.info("Attempting to login into pixiv")
        payload = {
            "captcha": "",
            "g_recaptcha_response": "",
            "password": password,
            "pixiv_id": username,
            "post_key": self._get_post_key(),
            "ref": "wwwtop_accounts_index",
            "return_to": "https://www.pixiv.net/",
            "source": "pc",
        }
        results = self.session.post(
            "https://accounts.pixiv.net/api/login?lang=en", data=payload
        )
        return results.status_code

    def _get_post_key(self):
        login_page = self.session.get(
            "https://accounts.pixiv.net/login?lang=en&source=pc&view_type=page&ref=wwwtop_accounts_index"
        )
        login_soup = BeautifulSoup(login_page.text, "html.parser")
        return login_soup.find("input", {"name": "post_key"})["value"]

    def _initialize_selenium(self):
        """Load Pixiv cookies into requests

        Migrate Pixiv cookies into selenium to make selenium
        logged in into Pixiv
        """
        Avalon.info("Initializing selenium")
        self.driver = webdriver.Chrome()

        # pixiv needs to be opened before cookies can be set
        self.driver.get(self.pixiv)

        # load cookies from requests session into selenium
        Avalon.info("Importing cookies into selenium from requests session")
        for name, value in self.session.cookies.get_dict().items():
            print(f"Adding cookie:  {name}:{value}")
            self.driver.add_cookie(
                {
                    "name": name,
                    "value": value,
                    "path": "/",
                    "domain": ".pixiv.net",
                    "secure": True,
                }
            )

    def get_large_image(self, link):
        """Find the large image URL for an illustration

        Use XPATH and beautiful soup to find the largest image's URL
        for a certain illustration
        """
        try:
            self.driver.get(self.pixiv + link)
            self.driver.switch_to.window(self.driver.window_handles[0])

            # find image element by XPATH
            for i in range(10):
                try:
                    presentation_element = self.driver.find_element_by_xpath(
                        '//div[@role="presentation"]'
                    )
                    break
                except selenium.common.exceptions.NoSuchElementException:
                    time.sleep(i)

            # scroll to the image
            action = ActionChains(self.driver)
            action.move_to_element(presentation_element)

            # click the prompt buttons
            for _ in range(10):
                with contextlib.suppress(
                    selenium.common.exceptions.NoSuchElementException,
                    selenium.common.exceptions.ElementNotInteractableException,
                ):
                    if (
                        presentation_element.find_element_by_tag_name("button")
                        is not None
                    ):
                        presentation_element.find_element_by_tag_name("button").click()
                    else:
                        break

            # click on the image to load large image URL
            try:
                presentation_element.find_element_by_tag_name("img").click()
            except (
                selenium.common.exceptions.ElementNotVisibleException,
                selenium.common.exceptions.ElementNotInteractableException,
            ):
                return presentation_element.find_element_by_tag_name(
                    "img"
                ).get_attribute("src")

            page_soup = BeautifulSoup(self.driver.page_source, "html.parser")
            return page_soup.find("div", {"role": "presentation"}).find("img")["src"]
        except selenium.common.exceptions.WebDriverException:
            print(link)
            traceback.print_exc()
            return False

    def get_popular_images(self):
        """Get top 50 images of the day

        returns a list of Illustration objects
        """

        # open selenium and load cookies
        self._initialize_selenium()

        # a list to hold all Illustration objects
        illustrations = []

        # Request page source
        self.driver.get("https://www.pixiv.net/ranking.php?mode=daily")

        # Parse page source
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        ranking_items = soup.find("div", {"class": "ranking-items"})

        # find illustration attributes
        for section in ranking_items.findAll("section", {"class": "ranking-item"}):
            author = section.find("a", {"class": "user-container"})["data-user_name"]
            author_id = section.find("a", {"class": "user-container"})["data-user_id"]
            data_id = section["data-id"]
            link = section.find("a", {"class": "work"})["href"]
            info = section.find("img")
            thumbnail = info["data-src"]
            tags = info["data-tags"].split(" ")
            large = self.get_large_image(link)
            Avalon.debug_info(
                f"Author={author}, ID={data_id}, Link={link}, Large={large}"
            )
            illustrations.append(
                Illustration(author, author_id, data_id, link, large, thumbnail, tags)
            )

        # close selenium window
        self.driver.close()

        return illustrations

    def download_large_image(self, illustration, directory):
        """Download the large image and append the object to cached list"""
        local_path = f'{directory}{illustration.large.split("/")[-1]}'
        Avalon.debug_info(f"Caching: {illustration.large}")
        headers = {"Referer": f"{self.pixiv}{illustration.link}"}
        image_request = requests.get(illustration.large, headers=headers)
        with open(local_path, "wb") as file:
            file_length = file.write(image_request.content)
            file.close()

        # check image integrity
        if int(image_request.headers["content-length"]) != file_length:

            # download was broken, try one more time
            image_request = requests.get(illustration.large, headers=headers)
            with open(local_path, "wb") as file:
                file_length = file.write(image_request.content)
                file.close()
            if int(image_request.headers["content-length"]) != file_length:
                return False

        # update illustration local cached path
        illustration.local_path = local_path

        if not illustration.local_path:
            Avalon.error(f"Unable to download {illustration.link}")
