#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

"""
toollist.py: Download the list of tools which are currently
             available in Kali Linux and compare them to
             the package list of katoolin3.

This only has a use for the maintainers of katoolin3.

Warning: This program has a high fault tolerance,
         it behaves more like the pirate-codex and 
         everything has to be checked manually.
"""

from html.parser import HTMLParser
import requests

try:
    import katoolin3
except ImportError:
    print("katoolin3.py needs to be in the same directory")
    exit(1)

class Color:
    red = "\033[1;31m"
    green = "\033[1;32m"
    reset = "\033[0m"

class Parser(HTMLParser):
    """
    This class parses the website tools.kali.org/tools-listing
    and extracts all categories and tools from it.

    Parsing rules:
        - Category names are enclosed in <h5></h5>
        - Tools in a category are inside a <ul class="lcp_catlist"></ul>
        - The tools themselves are inside a <li><a></a></li>
    """
    def __init__(self):
        super().__init__()
        self._old_data = self.handle_data
        self._packages = {}
        self._curr_cat = None
        self._inside_ul = False
        self._tag_count = 0

    def _new_cat(self, data):
        self._curr_cat = data
        self._packages[data] = []

    def handle_starttag(self, tag, attrs):
        if self._inside_ul:
            self._tag_count += 1

        if tag == "h5":
            self.handle_data = self._new_cat

        elif tag == "ul" and ("class", "lcp_catlist") in attrs:
            self._inside_ul = True
            self._tag_count = 0

        elif tag == "a":
            if self._inside_ul and self._tag_count == 2:
                self._packages[self._curr_cat].append(
                    dict(attrs)["href"].split("/")[-1]
                )
                self._tag_count = 0

    def handle_endtag(self, tag):
        if self.handle_data != self._old_data:
            self.handle_data = self._old_data

        if tag == "ul":
            self._inside_ul = False

    def feed(self, *args, **kwargs):
        super().feed(*args, **kwargs)
        return self._packages

class DictDiff:
    """
    This class compares dictionaries which are in
    the form of
    {
        key: [list of items]
    }
    and prints out the differences.
    """
    def __init__(self, base, new):
        self._base = base
        self._new = new

    def _new_item(self, item, indent=0):
        """
        This gets printed if something new was inserted
        """
        print("{}{}+{} {}".format(
            "\t" * indent,
            Color.green,
            Color.reset,
            item
        ))

    def _del_item(self, item, indent=0):
        """
        This gets printed if something was removed
        """
        print("{}{}-{} {}".format(
            "\t" * indent,
            Color.red,
            Color.reset,
            item
        ))

    def diff(self):
        """
        Create a diff of the two dictionaries
        """
        print("Changes relative to katoolins package list:")
        print()
        # First compare the categories
        rm_cats = set(self._base.keys()) - set(self._new.keys())
        new_cats = set(self._new.keys()) - set(self._base.keys())
        same_cats = set(self._new.keys()) & set(self._base.keys())

        for cat in new_cats:
            self._new_item(cat)

            for pkg in self._new[cat]:
                self._new_item(pkg, indent=1)

            print()

        for cat in rm_cats:
            self._del_item(cat)

            for pkg in self._base[cat]:
                self._del_item(pkg, indent=1)

            print()

        # Compare the lists:
        for cat in same_cats:
            rm_tools = set(self._base[cat]) - set(self._new[cat])
            new_tools = set(self._new[cat]) - set(self._base[cat])

            if len(rm_tools) + len(new_tools) == 0:
                continue

            print("{}:".format(cat))

            for tool in rm_tools:
                self._del_item(tool, indent=1)

            for tool in new_tools:
                self._new_item(tool, indent=1)

            print()


if __name__ == "__main__":
    r = requests.get("https://tools.kali.org/tools-listing", headers={
        # The website checks that certain headers are present:
        "Accept": "text/html",
        "Accept-Encoding": "gzip,deflate",
        "Connection": "close",
        "Host":  "tools.kali.org",
        "Referer": "https://tools.kali.org/",
        "User-Agent": "Luffa-plex Dill Pickle-inator"
    })
    r.raise_for_status()
    DictDiff(katoolin3.PACKAGES, Parser().feed(r.text)).diff()