#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 16:22:30 2019

@author: oem
"""
import difflib
from nltk.corpus import stopwords
import os
import numpy as np

import myHttp


words_to_skip = ['nobility', 'consort', 'princess', 'monarch', "heroes",
                 'countess', 'empress', 'queen', 'maharani', "catgirls",
                 'emira', 'begum', 'fictional', 'biblical', "bondgirls",
                 'religous', 'religon', 'bible', 'church', "transformers",
                 'roman', 'ancient', 'miss', 'pornography', "delta",
                 'playboy', 'mistress', 'county', 'counties', "zeta",
                 'Category', 'Pets', 'Penthouse', "Wikipedia", "chi",
                 "WWE", "violence", "pregnancy", "childbirth", "kappa",
                 "birth", "cancer", "oldest", "priests", "theta", "sigma",
                 "christian", "mystics", "babe", "duchess", "omega",
                 "Margravine", "spouse", "viceroy", "princess-abbesses",
                 "ruler", "vogue", "gravure", "idols", "beauty", "violence",
                 "WWE", "diva", "TNA", "glamour", "model", "allure", "sultan"
                 "valide", "raja", "permaisuri", "folklore", "prostitutes",
                 "courtesans", "baby", "character", "supervillan", "superhero",
                 "alpha", "sororities", "old", "college", "beta", "Template",
                 "Knockout",
                 ]


def is_bad_word(title, words_to_skip=words_to_skip):
    """
    Will return False if the title of the link has something that appears not
    suitable for the app or it's audience.
    """
    word_list = title.lower().split(" ")
    word_list = [new_word for word in word_list
                 for new_word in word.split('_')]
    word_list = [new_word for word in word_list
                 for new_word in word.split(':')]
    for word in ('list', 'women'):
        if word in word_list:
            word_list.remove(word)
    filtered_words = filtered_words = [word for word in word_list 
                                       if word not in stopwords.words('english')]
    bad_probs = [[difflib.SequenceMatcher(None, ref, word).ratio(), word, ref]
                 for word in filtered_words
                 for ref in words_to_skip]
    bad_probs = np.array(bad_probs)
    if len(bad_probs):
        mask = bad_probs[:, 0].astype(float) > 0.86
        if any(mask):
            return True
#            bad_words = ["%s (due to %s)" % (word, ref)
#                         for word, ref in bad_probs[mask][:, 1:]]
#            print("Title = ", title)
#            msg = "Highlighted bad keywords:\n\t*%s" % ('\n\t*'.join(bad_words))
#            print(msg)
    return False
#            input(" ")


def get_all_links(soup, wiki_url, good_filepath="", bad_filepath=''):
    """
    Will get all the links on the page. This has been designed to grab links
    for the root page, it hasn't been tested on other pages and may need
    modifications.
    """
    if os.path.isfile(good_filepath):
        all_links = list(np.load(good_filepath))
    else: all_links = []
    if os.path.isfile(bad_filepath):
        all_bad_links = list(np.load(bad_filepath))
    else: all_bad_links = []

    for a in soup.findAll("a"):
        attrs = a.attrs
        title = attrs.get("title")
        href = attrs.get("href")
        if not href or '#' in href: continue
        wiki_link = "%s/%s" % (wiki_url, href.strip("/"))
        
        if wiki_link in all_links: continue
        if wiki_link in all_bad_links: continue

        if title:
            has_bad_word = is_bad_word(title, words_to_skip)
            if has_bad_word: all_bad_links.append(wiki_link); continue
            title = title.lower().replace(" ", "_")
        else:
            continue
        if href and '#' not in href:
            tmp = href.strip("/")
            tmp = tmp[tmp.rfind("/"):]
            tmp = tmp.lower().strip("/")
            if tmp == title:
                wiki_link = "%s/%s" % (wiki_url, href.strip("/"))
                all_links.append(wiki_link)
    
    if good_filepath:
        np.save(good_filepath, all_links)
    if bad_filepath:
        np.save(bad_filepath, all_bad_links)
    
    return all_links


def load_save_all_pages(folderpath, all_links, wiki_url, do_soup=True):
    """
    Will save all the HTML pages in the list all_links in the folder given
    """
    remove_me = ['https://en.wikipedia.org', wiki_url, 'wiki', 'https://']
    all_soups = {}
    for link in all_links:
        name = link
        for remover in remove_me:
            name = name.replace(remover, "")
        name = name.strip('/')
        name = name + ".html"
        print(name)
        link_filepath = os.path.join(folderpath, name)
        
        soup = myHttp.get_page_soup(link, link_filepath, do_pause=True,
                                    do_soup=do_soup)
        
        all_soups[name[:-5]] = soup
        print("Done %s" % name[:-5])
        
        
    return all_soups