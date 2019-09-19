#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 10:27:13 2019

@author: oem
"""
import nltk
import re
import pandas as pd
import bs4

import rootPage

bad_words = ['Wikipedia', "Australia", "Senate", "Animal", "Bulldog",
             "army", "prize", "war", "Advertiser"]


def remove_section_between_h2(soup, bad_sections=['reference', 'bibliograph',
                                                   'see also', 'contents',
                                                   'navigation', "statistics"]
                             ):
    """
    Will remove sections from the soup between 2 elements given their inner
    text is the same as the section name.
    """
    for header in soup.findAll("h2"):
        txt = re.sub("\[.*\]", "", header.text)
        for section in bad_sections:
            if section in txt.lower():
                for elt in header.nextSiblingGenerator():
                    if elt.name == "h2":
                        break
                    for sib in elt.next_siblings:
                        if isinstance(sib, (bs4.NavigableString,
                                            bs4.element.NavigableString,
                                            bs4.Comment, 
                                            bs4.element.Comment)):
                            continue
                        sib.decompose()
    return soup


def check_for_nouns(txt, threshold=1):
    """
    Will check how may of the words have proper nouns in and will return True
    or False depending on the percentage that are proper nouns.
    """
    words = nltk.word_tokenize(txt)
    if not words or len(words) > 3: return False
    proper_nouns = []
    for word, pos in nltk.pos_tag(words):
        if pos == "NNP": proper_nouns.append(word)
    
    if (len(proper_nouns) / len(words)) >= threshold:
        return True
    else:
        return False
    

def get_name_links_from_text(soup, wiki_url):
    names_and_links = {'names': [], 'links': []}
    excluders = ["(", ")", "'s", ",", "_", '[', ']', ":"]
    for a in soup.findAll("a"):
        if not a: continue        
        txt = a.attrs.get('title')
        if not txt: continue
        if any(exc in txt for exc in excluders): continue
        if rootPage.is_bad_word(a.text): continue        

        has_good_nouns = check_for_nouns(txt, 1)
        if not has_good_nouns: continue

        name = a.attrs.get('title')
        
        s = [i for i in re.findall("[^a-zA-Z]+", name) if i.strip()]
        badStr = len(''.join(s)) > 5
        if badStr: continue
        
        link = a.attrs.get('href')
        
        if link and name:
            names_and_links['links'].append("%s/%s" % (wiki_url, link))
            names_and_links['names'].append(name)

    return names_and_links


def get_name_links_from_ulist(soup, wiki_url):
    """
    Will get the names and links of women in lists on wiki pages.
    """
    u_lists = soup.findAll("ul")
    excluders = ["(", ")", "'s", ":", ",", "_", '[', ']']
    names_and_links = {'names': [], 'links': []}
    for ul in u_lists:
        all_li = ul.findAll("li")
        for li in all_li:
            a = li.a
            if a is None: continue
            
            attrs = a.attrs
            title = attrs.get("title")
            if title is None: continue
            words = nltk.word_tokenize(title)
            
            num_words = len(words)
            if num_words > 3 or num_words < 2: continue
            if any(exc in title for exc in excluders): continue
            
            has_good_nouns = check_for_nouns(title, 1)
            if not has_good_nouns: continue

            link = attrs.get("href")
            if link is None: continue
            
            names_and_links['links'].append("%s/%s" % (wiki_url, link))
            names_and_links['names'].append(title)
    
    return names_and_links


def get_name_links_from_table(soup, wiki_url):
    """
    Will get the names and links of women in tables on wiki pages.
    """
    tables = soup.findAll("table")
    names_and_links = {'names': [], 'links': []}
    for table in tables:
        if len(table.findAll("tr")) > 20:
            headers = [i.text.strip("\n").strip() for i in table.findAll("th")]
            headers = [i.lower() for i in headers]
            headers = [re.sub("\(.*\)", "", i) for i in headers]
            
            name_strs = ['full name', 'name', 'representative', 'winner', 'artist',
                         'actress', 'actor', 'ceo', 'driver', 'champion',
                         'gold', 'secretary', 'minister', 'wrestler',
                         'player', 'laureate', '1st']
            for name_ind, name in enumerate(name_strs):
                found = False
                for header in headers:
                    if header.lower() in name.lower():
                        found = True
                        break
                if found:
                    break
            else:
                print(soup.title)
                print("Can't find the name in the table headers")
                print("headers = ", headers)
                return names_and_links
            
            for row in table.findAll("tr"):
                table_entries = row.findAll("td")
                table_entries = [i for i in table_entries if i.text.strip()]
                if not len(table_entries): continue
                if len(table_entries) <= name_ind: continue
                name_entry = table_entries[name_ind]
                a = name_entry.a
                if a is None: continue
                attrs = a.attrs
                title = attrs.get('title')
                if title is None: continue
                if "(page does not exist)" in title: continue
                title = re.sub("\(.+\)", "", title)
            
                has_good_nouns = check_for_nouns(title, 1)
                if not has_good_nouns: continue

                link = attrs.get('href')
                if link is None: continue
                
                names_and_links['links'].append("%s/%s" % (wiki_url, link))
                names_and_links['names'].append(title)
    return names_and_links


def get_all_women_links(all_list_soups, wiki_url):
    """
    Will get all the wiki links to the women's pages and save them as a csv
    file in the metadata folder.
    """
    soups_to_ignore = ['women']
    
    names_links = {'names': [], 'links': [], 'category': []}
    lists_completed = []
    for name in all_list_soups:
        if any(name.lower() == j.lower() for j in soups_to_ignore): continue
        print("name of soup: %s" % name)
        soup = all_list_soups[name]
        soup = remove_section_between_h2(soup)
    
        names_and_links = get_name_links_from_table(soup, wiki_url)
        for i, key1 in enumerate(names_and_links):
            for list_item in names_and_links[key1]:
                names_links[key1].append(list_item)
                if i == 0:
                    names_links['category'].append(name)
    
        names_and_links = get_name_links_from_ulist(soup, wiki_url)
        for i, key1 in enumerate(names_and_links):
            for list_item in names_and_links[key1]:
                names_links[key1].append(list_item)
                if i == 0:
                    names_links['category'].append(name)
    
        lists_completed.append(name)
    df = pd.DataFrame(names_links)
    df = df.drop_duplicates("links")
    df.to_csv("./metadata/Women_and_Links.csv", index=False)
    return df