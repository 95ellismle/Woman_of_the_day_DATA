#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 19:52:43 2019

@author: oem
"""

import requests as rq
import bs4
import os
import time
import numpy as np


class GetPage(object):
    """
    Stores methods needed for grabbing web page data.
    
    Inputs:
        * url           ->  The url to download
        * must_contain  ->  Any strings the website must have.
    
    Methods:
        * get    ->  Will download the webpage
        * check  ->  Will check the web page has been downloaded properly
        * save   ->  Will save the webpage as an html file.
    """
    def __init__(self, url, must_contain=[], soup=False, throw_error=False):
        self.bad_site = False
        self.url = url
        self.no_url = True
        self.soup = soup
        self.error = throw_error
        if not self.soup:
            self.no_url = False
            self._get(url)    
            self._check(must_contain)
            self.soup = bs4.BeautifulSoup(self.R.text, 'lxml')
    
    def _get(self, url):
        """
        Will download a webpage as a requests.models.Response class.
        
        Inputs:
            * url  ->  The url to download
        """
        user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
        timeout = 2
        trigger = True
        while (timeout < 500 and trigger):
            try:
                self.R = rq.get(url, headers={'user-agent':user_agent}, timeout=timeout)
                trigger = False
                break
            except (rq.exceptions.ConnectTimeout, rq.exceptions.Timeout):
                print("Timed out increasing timeout and trying again")
                timeout += 200
        else:
            raise SystemExit("""Sorry I couldn't download the webpage for the url:
                %s
                
                Used a timeout of %i seconds and I couldn't connect.
                
                Please make sure the url is correct!"""%(url, timeout))
    
    # TODO: Need to get blocked from more site in order to recognise them!
    def _check(self, must_contain):
        """
        Will check the downloaded webpage. This will work by checking if the 
        word 'blocked' is in the webpage and if the webpage is very small. Or if
        the website doesn't contain the requesite words.
        
        Inputs:
            None
        """
        txt = self.R.text
        for word in must_contain:
            triggered = False
            if word not in txt:
                print("""The website does not contain the substring '%s'. I'm
                      assuming this is a bad website!"""%word)
                self.bad_site = True
            if triggered:
                self.__exit("Site doesn't contain the words:\n\t*%s"%'\n\t*'.join(must_contain))
        
        if self.R.status_code > 300:
            self.__exit("Bad Status Code") 
            
        if 'blocked' in txt.lower():
            if len(txt) < 3000:
                self.bad_site = True
    
    def __exit(self, msg):
        """
        Will exit safely and print useful info.
        
        Params:
            * msg    ->  The error message printed out.
        """
        print("\t"+msg)
        print("\tURL:          %s"%self.url)
        print("\tStatus Code:  %i"%self.R.status_code)
        Ofilename = "./Err"
        filename = Ofilename + ".html"
        count = 0
        if os.path.isfile(filename):
            while os.path.isfile(filename):
                filename = Ofilename + "_(%i).html" % count
                with open(filename, 'w') as f:
                    f.write(self.R.text)
        else:
            with open("./Err.html", 'w') as f:
                f.write(self.R.text)
        print("\tSaved page as ./Err.html")
        if self.error:
            raise SystemExit("Webpage Error")
    
    def save_page(self, filename):
        """
        Will save the webpage text as an html file. The workflow for this is 
        given below:
            * Find any folders in the name and create them.
            * If there is no extension use  .html
            * Save the file in the created folders
        
        Inputs:
            * filename  ->  The name of the file that is being saved.
        """
        # Create any folders.
        if '/' in filename:
            folderpath = filename[:filename.rfind('/')]
            if folderpath and not os.path.isdir(folderpath):
                os.makedirs(folderpath)
            filename = filename.replace(folderpath, '').strip('/')
        else:
            folderpath = os.getcwd()
            
        # Use html as default extension
        if '.' not in filename:
            filename = filename + '.html'
        
        if folderpath[-1] != '/': folderpath = folderpath + '/'
        
        # Save
        self.filepath =  os.path.abspath(folderpath.strip() + filename.strip())
        with open(self.filepath, 'w') as f:
            if self.no_url:
                f.write(str(self.soup))    
            else:
                txt = self.R.text
                txt = txt[txt.find("AGM plants have been through a rigorous trial and assessment programme. They are:"):txt.find("Did you find the information you were looking for?")]
                f.write(txt)


def __request_get(url, do_pause=True,
                  user_agent='My Scraper, Name: Matt Ellis Contact: 95ellismle@gmail.com'):
    """
    Will just get a webpage and return the requests object
    """
    if do_pause: time.sleep(abs(np.random.normal(0.5, 0.5)))
    
    headers = {'user-agent': user_agent}
    r = rq.get(url, headers)
    print("Making Request at: %s" % url)
    if r.status_code < 300:
        return r
    else:
        print("Failed request for:\n\t%s" % url)
        return False


def get_page_soup(url, filename=False, do_pause=True, do_soup=True,
                  user_agent='My Scraper, Name: Matt Ellis Contact: 95ellismle@gmail.com'):
    """
    Will return the soup from a webpage.
    If unsucessful then will return False
    """
    if filename == False:
        r = __request_get(url, do_pause, user_agent=user_agent)
        if r is False: return False
    else:
        soup = open_html_page(filename, do_soup=do_soup)
        if soup is False:
            r = __request_get(url, do_pause, user_agent=user_agent)
            if r is False: return False
            save_html_page(r, filename)
        else:
            return soup
    if do_soup:
        return bs4.BeautifulSoup(r.text, features="lxml")
    return r



def save_html_page(obj, filename):
    """
    Will save a html page in the location specified. If the object isn't
    compatible then will return False.
    """
    # Make sure the filename has the .html extension and isn't too long
    if len(filename) > 240:
        filename = filename[:240]
    if '.html' != filename[-5:]:
        filename = filename[:filename.rfind('.')+1] + 'html'

    Ofilename = os.path.abspath(filename)
    count = 0
    while os.path.isfile(filename):
        filename = Ofilename + "_(%i)" % count
        count += 1
    
    if type(obj) == bs4.BeautifulSoup:
        text = str(obj)
    else:
        try:
            text = obj.text
        except:
            print("Obj = ", obj)
            print("type(obj) = ", type(obj))
            print("Can't save obj as it is not the right type")
            print("It should be a BeautifulSoup or Requests.get object")
            return False
    
    # Check if the folder exists
    folders = filename[:filename.rfind('/')]
    if not os.path.isdir(folders):
        os.makedirs(folders)

    # Create the file
    with open(filename, 'w') as f:
        f.write(text)


def open_html_page(filename, do_soup=True):
    """
    Will open an html file and return a soup object.
    """
    if not os.path.isfile(filename):
        print("Cannot find file:\n\t%s" % filename)
        return False

    with open(filename, 'r') as f:
        txt = f.read()
    if do_soup:
        soup = bs4.BeautifulSoup(txt, "lxml")
        return soup
    else:
        return txt
