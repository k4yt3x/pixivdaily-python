#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Illustration
Author: K4YT3X
Date Created: Feb 24, 2018
Last Modified: June 22, 2019

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt

(C) 2018-2019 K4YT3X
"""


class Illustration:
    """Illustration Class
    Each illustration is an object of this class.
    """

    def __init__(
        self, author, author_id, data_id, link, large, thumbnail, tags, local_path=None
    ):
        self.author = author
        self.author_id = author_id
        self.data_id = data_id
        self.link = link
        self.large = large
        self.thumbnail = thumbnail
        self.tags = tags
        self.local_path = local_path
        self.available = True
