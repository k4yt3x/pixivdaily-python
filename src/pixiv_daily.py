#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Pixiv Daily Server
Author: K4YT3X
Date Created: Feb 24, 2018
Last Modified: July 30, 2019

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt

(C) 2018-2019 K4YT3X
"""

# local imports
from pixiv import Pixiv

# built-in imports
import argparse
import datetime
import queue
import shutil
import tempfile
import threading
import time
import traceback

# third-party imports
from avalon_framework import Avalon
from telegram_channel import TelegramChannel

# master version number
VERSION = "1.5.0"

# Pixiv/Telegram credentials
PIXIV_USERNAME = ""
PIXIV_PASSWORD = ""
TELEGRAM_BOT_TOKEN = ""

# other static variables
DEBUG_CHANNEL = "@example"


def process_arguments():
    """This function parses all command line arguments"""
    parser = argparse.ArgumentParser()
    control_group = parser.add_argument_group("Controls")
    control_group.add_argument(
        "-s", "--serve", help="start feeding images to channels", action="store_true"
    )
    control_group.add_argument(
        "-n",
        "--now",
        help="post immediately for once and enter normal cycle",
        action="store_true",
    )
    control_group.add_argument(
        "-v", "--version", help="prints program version and exit", action="store_true"
    )
    control_group.add_argument(
        "-m", "--manual-login", help="login manually in selenium", action="store_true"
    )
    return parser.parse_args()


def daemon():
    """Daemon thread function

    This function should be run in a separate thread
    from the main thread. It updates the image lists
    and signals the bots to send images every hour.
    """
    while True:
        hours_left = 23 - datetime.datetime.now().hour
        minutes_left = 59 - datetime.datetime.now().minute

        # 0:00 midnight everyday
        if (
            datetime.datetime.now().hour == 0
            and datetime.datetime.now().minute == 0
            or not args.serve
            or args.now
        ):

            illustrations = pixiv.get_popular_images()

            # download all illustration images
            cache_dir = tempfile.mkdtemp()

            for illustration in [i for i in illustrations if i.large]:
                try:
                    if pixiv.download_large_image(illustration, cache_dir) is False:
                        continue
                except Exception:
                    traceback.print_exc()
                    try:
                        if pixiv.download_large_image(illustration, cache_dir) is False:
                            continue
                    except Exception:
                        traceback.print_exc()
                        continue

            channel.send(illustrations)
            shutil.rmtree(cache_dir)
            Avalon.debug_info("Sending sequence completed")

            # run only once in test mode
            if not args.serve:
                exit(0)

            # if the script finishes within one minute
            # wait until the minute passes to prevent duplicated launches in one day
            while datetime.datetime.now().minute == 0:
                if not signal_queue.empty():
                    Avalon.debug_info("Daemon thread exiting")
                    exit(0)
                time.sleep(0.5)
            args.now = False
        else:
            width, height = shutil.get_terminal_size((80, 20))
            spaces = (
                width
                - len(
                    f"[Cooling Down]: {hours_left} hours {minutes_left} minutes until next round"
                )
                - 1
            ) * " "
            print(
                f"{Avalon.FG.G}{Avalon.FM.BD}[Cooling Down]: {hours_left} hours {minutes_left} minutes until next round{spaces}{Avalon.FM.RST}",
                end="\r",
            )
            if not signal_queue.empty():
                Avalon.debug_info("Daemon thread exiting")
                exit(0)
            time.sleep(0.5)


# /////////////////// Execution /////////////////// #

if __name__ == "__main__":
    args = process_arguments()

    if args.version:
        print(f"Pixiv Overall Daily Rankings Version: {VERSION}")
        print("Copyright 2018-2019, K4YT3X, All rights reserved.")
        exit(0)

    # initialize a queue to hold signals
    signal_queue = queue.Queue()

    pixiv = Pixiv(PIXIV_USERNAME, PIXIV_PASSWORD)
    channel = TelegramChannel(TELEGRAM_BOT_TOKEN)

    # if serve is not explicitly specified, send to debug channel
    if not args.serve:
        channel.channel = DEBUG_CHANNEL

    while True:
        try:
            daemon_thread = threading.Thread(target=daemon)
            daemon_thread.start()

            try:
                daemon_thread.join()
            except KeyboardInterrupt:
                Avalon.warning("Exit signal received")
                signal_queue.put(None)
                daemon_thread.join()
                exit(1)
        except Exception:
            traceback.print_exc()
