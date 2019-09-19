#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 12:49:46 2019

@author: oem
"""
import pandas as pd
import time
import json
import os

import myHttp

print("Adding the inspiration Women from googling lists of them")

do_df = False
if os.path.isfile("./metadata/Women_and_Links.csv"):
    df = pd.read_csv("./metadata/Women_and_Links.csv")
    do_df = True

def make_folderpath(name, extra_folders=""):
    """
    Will make the folderpath for the woman's profile
    """
    folderpath = "./Women_Profiles/%s" % name
    if extra_folders != "":
        folderpath = "%s/%s" % (folderpath, extra_folders)
    folderpath = folderpath.replace(" ", "_")
    if not os.path.isdir(folderpath):
        os.makedirs(folderpath)
    return folderpath


def get_wiki_page(name):
    """
    Will search ecosia for the wiki page
    """
    time.sleep(0.5)
    print(name)
    search_str = "https://www.ecosia.org/search?q=%s+wiki" % '+'.join(name.split(' '))
    print(search_str)
    search_page = myHttp.GetPage(search_str, must_contain=[name])
    if not search_page:
        print("Couldn't find link for %s. Ecosia Page Dodgy." % name)
        return False
    soup = search_page.soup
    for a  in soup.find_all("a"):
        if a is None: continue
        attrs = a.attrs
        if attrs is None: continue
        href = attrs.get('href')
        if href is None: continue
        if 'https://en.wikipedia' in href and name.split(" ")[0] in href:
            break
    else:
        print("Couldn't find link for %s" % name)
        return False
    print(href)
    return href


# Remove any duplicates from the Inspirational women list
with open('./metadata/Inspirational_Women.list', 'r') as f:
    inps_wom_list = f.read().split("\n")
    inps_wom_list = [i for i in inps_wom_list if i]
    inps_wom_list = list(set(inps_wom_list))

with open("./metadata/Inspirational_Women.list", 'w') as f:
    f.write('\n'.join(inps_wom_list))


# Read any women that have already been processed
if do_df:
    Insp_df = pd.read_csv("./metadata/Inspirational_Women_Links.csv")
    dictionary = {i: list(Insp_df[i]) for i in Insp_df.columns}
    extra_links = {name: link for name, link in zip(dictionary['names'], dictionary['links'])}
else:
    extra_links = {}

# Find any women that aren't already in the database
if do_df:
    count = 0
    missing_women = []
    check_names = [i.replace(" ", "") for i in df['names']]
    for name in inps_wom_list:
        check = name.replace('’', "'").replace(" ","")
        if check not in check_names:
            missing_women.append(name)
            count += 1
        else:
            for i, check_name in enumerate(check_names):
                if check == check_name:
                    link = df.iloc[i]['links']
                    true_name = df.iloc[i]['names']
                    extra_links[true_name] = link

    # Get the women's wiki link
    for name in missing_women:
        if name not in extra_links:
            extra_links[name] = get_wiki_page(name)
else:
    for name in inps_wom_list:
        if name not in extra_links:
            extra_links[name] = get_wiki_page(name)

def remove_key(D, key):
    if D.get(key) is not None:
        D.pop(key)


# Add any women that have different names to those I would like so haven't been
#        processed
remove_key(extra_links,"Dame Judi Dench")
extra_links['Judi Dench'] = 'https://en.wikipedia.org/wiki/Judi_Dench'

remove_key(extra_links,"Dr. Mae Jemison")
extra_links['Mae Jemison'] = 'https://en.wikipedia.org/wiki/Mae_Jemison'

remove_key(extra_links,"Dr Ingrid Mattson")
extra_links['Ingrid Mattson'] = 'https://en.wikipedia.org/wiki/Ingrid_Mattson'

remove_key(extra_links,"Anais Nin")
extra_links['Anaïs Nin'] = 'https://en.wikipedia.org/wiki/Ana%C3%AFs_Nin'

remove_key(extra_links,"Sinead O'Connor")
extra_links['Sinéad O\'Connor'] = 'https://en.wikipedia.org/wiki/Sin%C3%A9ad_O%27Connor'

remove_key(extra_links,"Senator Kirsten Gillibrand")
extra_links['Kirsten Gillibrand'] = 'https://en.wikipedia.org/wiki/Kirsten_Gillibrand'

extra_links['Vigdís Finnbogadóttir'] = 'https://en.wikipedia.org/wiki/Vigd%C3%ADs_Finnbogad%C3%B3ttir'

remove_key(extra_links,"Graca Machel")
extra_links['Graça Machel'] = 'https://en.wikipedia.org/wiki/Gra%C3%A7a_Machel'

remove_key(extra_links,'Lil’ Kim')
extra_links['Lil\' Kim'] = 'https://en.wikipedia.org/wiki/Lil%27_Kim'

remove_key(extra_links,'Wangaari Mathaai')
extra_links['Wangari Maathai'] = 'https://en.wikipedia.org/wiki/Wangari_Maathai'

remove_key(extra_links,'Brene Brown')
extra_links['Brené Brown'] = 'https://en.wikipedia.org/wiki/Bren%C3%A9_Brown'

extra_links['Estée Lauder'] = 'https://en.wikipedia.org/wiki/Est%C3%A9e_Lauder_(businesswoman)'

remove_key(extra_links, 'bell hooks')
extra_links['Bell Hooks'] = 'https://en.wikipedia.org/wiki/Bell_hooks'




# Change format of the data storage to make it easier to write with pandas
Insp_df = {'names':[], 'links':[], 'category':[]}
for i in extra_links:
    Insp_df['names'].append(i)
    Insp_df['links'].append(extra_links[i])
    Insp_df['category'].append('Unknown')

Insp_df = pd.DataFrame(Insp_df)
Insp_df = Insp_df[Insp_df['links'] != False]
Insp_df['profile_path'] = Insp_df['names']
Insp_df['profile_path'] = Insp_df['profile_path'].apply(make_folderpath)

bad_folds = Insp_df['profile_path'].apply(os.path.isdir)
if len(bad_folds) < 1:
    print("Can't find *\n\t%s" % "*\n\t".join(list(bad_folds['names'])))
    print("\nIn the ./Women_Profiles folder")


def get_first_phrase(txt, phrases):
    """
    Find which phrase comes first in some txt. If none of the phrases appear we
    return False.
    """
    min_score = len(txt) + 100
    first_phrase = False
    for phrase in phrases:
        score = txt.find(phrase)
        if score > -1 and score < min_score:
            min_score = score
            first_phrase = phrase

    return first_phrase


# Now get the category the women fits into (may be helpful later)
def get_cat_from_summ(txt):
    """
    Will try and get the category from the summary of the wiki txt
    """
    # Find which phrase comes first
    first_phrase = get_first_phrase(txt, ['served as', 'is a', 'was a',
                                          'was one', 'is one', 'was the',
                                          'is the'])
    if first_phrase is False:
        return False

    txt = txt.split(first_phrase)[1]
    txt = txt.lstrip('n ')
    txt = txt.split('.')[0]

    first_phrase = get_first_phrase(txt, ['who', 'from', 'since', ','])
    if first_phrase is not False:
        txt = txt.split(first_phrase)[0]

    if len(txt.split(' ')) < 20:
        return txt.strip()

    return False

def get_category(profile_path):
    """
    Will attempt to work out the category of a person from the all_info.json
    file.
    """
    filepath = "%s/all_info.json" % profile_path
    if not os.path.isfile(filepath):
        print("I can't find the file: %s" % filepath)
        return "no file"

    with open(filepath, 'r') as f:
        D = json.load(f)

    if D['info_box'] is not False:
        good_keys = ['occupation', "occupation(s)", 'known\xa0for', 'known for']
        for curr_key in D['info_box'].keys():
            if curr_key.lower() in good_keys:
                return "%s: %s" %(curr_key, D['info_box'][curr_key])

    txt = D['summary']
    if txt is not False:
        cat = get_cat_from_summ(txt)
        return cat

    return False



Insp_df['category'] = Insp_df['profile_path']
Insp_df['category'] = Insp_df['category'].apply(get_category)


# Now update the ./metadata/Extra_Women.csv file to make sure the names appear
# in the Women_and_Links.csv file.
Insp_df.to_csv("./metadata/Extra_Women.csv", index=False)


