# Class used to interface with halfbakery
import requests, re, json, datetime, dateparser
import urllib
from bs4 import BeautifulSoup as bs


class Page():
    def __init__(self, session, url):
        # Fetch and store a page from the internet
        response = session.get(url)
        self.response=response
        self.headers = response.headers
        self.apparent_encoding=response.apparent_encoding
        self.status_code=response.status_code
        self.url=url
        self.text=self.response.text
        ctype=self.headers.get('Content-Type').split(";")
        self.mime_type=ctype[0]
        self.charset=ctype[1].split("=")[1]
        self.date=dateparser.parse(self.headers.get("Date"))
        self.domain=urllib.parse.urlparse(url).netloc
        if response.status_code>=200 and response.status_code<300:
            self.raw = response.content
        else:
            self.raw = None

    def content(self):
        if "text" in self.mime_type:
            return self.response.text
        else:
            return self.raw

    def html_links(self):
        try:
            soup = self.content()
        except SyntaxError as e:
            print (e)
            return None
