#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Telegram Channel
Author: K4YT3X
Date Created: Feb 24, 2018
Last Modified: June 22, 2019

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt

(C) 2018-2019 K4YT3X
"""
from avalon_framework import Avalon
from telegram.ext import Updater
import calendar
import datetime
import socket
import telegram
import traceback


class TelegramChannel:
    def __init__(self, token):
        self.updater = Updater(token)
        self.pixiv = "https://www.pixiv.net"
        self.channel = "@pixiv_daily"

    def send(self, illustrations):
        # Generate today's date
        today = datetime.datetime.today()
        long_date = f"{calendar.month_name[today.month]} {today.day}, {today.year}"

        # Send message and record message ID
        date_message_id = self.updater.bot.send_message(
            chat_id=self.channel, text=long_date
        )["message_id"]

        # Pin message in channel by ID
        self.updater.bot.pin_chat_message(
            chat_id=self.channel, message_id=date_message_id
        )

        # Send every image in the list
        for illustration in [i for i in illustrations if i.local_path]:

            caption = [
                f"Author: [{illustration.author}]({self.pixiv}/member.php?id={illustration.author_id})",
                f"Illustration ID: [{illustration.data_id}]({self.pixiv}{illustration.link})",
            ]

            # create captions line
            tag_strings = []
            for tag in illustration.tags:
                tag_strings.append(
                    f"[#{tag}]({self.pixiv}/search.php?s_mode=s_tag_full&word={tag})"
                )
            caption.extend([f'Tags: {", ".join(tag_strings)}'])

            # start sending image
            try:
                Avalon.debug_info(f"Sending: {illustration.local_path}")
                self.updater.bot.send_photo(
                    chat_id=self.channel,
                    photo=open(illustration.local_path, "rb"),
                    timeout=60,
                    parse_mode=telegram.ParseMode.MARKDOWN,
                    caption="\n".join(caption),
                )
                continue

            # if sending failed, retry 5 times
            except Exception:
                counter = 0
                while counter < 5:
                    try:
                        Avalon.debug_info(f"Sending: {illustration.local_path}")
                        self.updater.bot.send_photo(
                            chat_id=self.channel,
                            photo=open(illustration.local_path, "rb"),
                            timeout=60,
                            parse_mode=telegram.ParseMode.MARKDOWN,
                            caption="\n".join(caption),
                        )
                        break
                    except Exception:
                        traceback.print_exc()
                        counter += 1
                continue
            except (telegram.error.TimedOut, socket.timeout, KeyboardInterrupt):
                traceback.print_exc()
                continue
