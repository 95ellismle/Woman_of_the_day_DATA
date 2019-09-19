 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 19:37:49 2019

@author: oem
"""
import pandas as pd
import re
import os
import json

import myHttp
import rootPage
import getWomenLinks as womLink
import parse_women as womParse
import Inspirational_Women

init = True


wiki_url = "https://en.wikipedia.org"
root_url = "%s/wiki/Lists_of_women" % wiki_url


def open_list_file(filename):
    """
    Will open a .list file (normally found in metadata folder).
    """
    with open(filename, "r") as f:
        ltxt = [i for i in f.read().split("\n") if i]
    return ltxt



def person_is_male_or_female(filename):
    """
    Will determine from the html file whether the person in question is likely
    female or male.
    """
    with open(filename, 'r') as f:
        txt = f.read().lower().split(' ')
        her_count = txt.count("her")
        his_count = txt.count("his")
        she_count = txt.count("she")
        he_count = txt.count("he")

        if he_count == 0 and she_count > 1:
            return 'female'
        elif she_count == 0 and he_count > 1:
            return 'male'
        elif he_count <= 1 and she_count <= 1:
            return False

        if she_count / he_count > 3:
            return 'female'
        elif he_count / she_count > 3:
            return 'male'
        else:
            return False

        if his_count == 0 and her_count > 0:
            return 'female'
        elif her_count == 0 and his_count > 0:
            return 'male'
        elif his_count == 0 and her_count == 0:
            return False

        if her_count / his_count > 3:
            return 'female'
        elif his_count / her_count > 3:
            return 'male'
        else:
            return False


if init:


    def tidy_links(link):
        if link.count("https://") > 1:
            return False
        if 'en.wikipedia' not in link:
            return False
        else:
            return link.replace("//", "/").replace("https:/", "https://")


    def tidy_name(name):
        """
        Will remove extraneous info from the name such as '(singer)' and generally
        tidy it.
        """
        name = re.sub("\(.*\)", "", name)
        name = name.strip().replace("_", " ")
        return name


    root_soup = myHttp.get_page_soup(root_url, "HTML/root.html")

    print("Getting list links")
    all_root_links = rootPage.get_all_links(root_soup, wiki_url,
                                   "./metadata/all_root_links.npy",
                                   "./metadata/all_bad_root_links.npy")
    print("Loading and/or saving pages")
    all_list_soups = rootPage.load_save_all_pages("./HTML/List_Pages/",
                                                  all_root_links,
                                                  wiki_url)

    print("Getting links for women's pages.")
    df = womLink.get_all_women_links(all_list_soups, wiki_url)

    # Now add women from the following categories
    extra_list = ['https://en.wikipedia.org/wiki/Category:American_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Australian_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Belgian_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Brazilian_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:British_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Canadian_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:English_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Filipino_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:French_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:German_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Indian_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Iranian_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Japanese_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Lebanese_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Malaysian_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Mexican_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:New_Zealand_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Nigerian_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:South_Korean_female_pop_singers',
                  'https://en.wikipedia.org/wiki/Category:Spanish_female_pop_singers']
    all_links = []
    all_categories = []
    for url in extra_list:
        name = url[url.rfind('Category:'):]
        filename = "./HTML/List_Pages/%s" % (name)
        soup = myHttp.get_page_soup(url, filename)
        links = rootPage.get_all_links(soup, wiki_url)
        for link in links:
            all_categories.append(name)
            all_links.append(link)
    df_extra = {'names': [], 'links':[], 'category':[]}
    for link, cat in zip(all_links, all_categories):
        name = link[link.rfind('/')+1:]
        df_extra['names'].append(name)
        df_extra['links'].append(link)
        df_extra['category'].append(cat)
    df_extra = pd.DataFrame(df_extra)
    df = df.append(df_extra)

    bad_names = []
    for name in df['names']:
        if any(j in name for j in (':', ';', '\'s')):
            bad_names.append(name)

        good_nouns = womLink.check_for_nouns(name, 1)
        if not good_nouns:
            bad_words = [word for word in name.split(' ') if word in ('and', 'for')]
            if len(bad_words):
                bad_names.append(name)

    # Add those names and links in the manually compiled Extra_Women file
    df_manual = pd.read_csv("./metadata/Extra_Women.csv")
    rootPage.load_save_all_pages("./HTML/Women/", list(df_manual['links']),
                                 wiki_url, do_soup=False)
    df = df.append(df_manual)
    df.index = range(len(df))
    df.drop_duplicates('links')
    df['names'] = df['names'].apply(tidy_name)
    df['links'] = df['links'].apply(tidy_links)
    df = df[df['links'] != False]
    if len(df[df['names'] == 'Rosa Parks']) == 0:
        print("No Rosa Parks -177!")
        raise SystemExit("BREAK")


    for name in bad_names:
        df = df[df['names'] != name]
    if len(df[df['names'] == 'Rosa Parks']) == 0:
        print("No Rosa Parks -183!")
        raise SystemExit("BREAK")

    all_links = []
    for fN in os.listdir('./HTML/Women'):
        gender = person_is_male_or_female('./HTML/Women/' + fN)
        if gender == 'male':
            all_links.append(fN.replace(".html", ""))

    for bad_name in all_links:
        df = df[~df['links'].str.contains(bad_name)]
    if len(df[df['names'] == 'Rosa Parks']) == 0:
        print("No Rosa Parks -196!")
        raise SystemExit("BREAK")

    # Attach the filenames to the df and more tidying of data
    df['links'] = df['links'].apply(tidy_links)
    df = df[df['links'] != False]
    df = df.drop_duplicates('links')
    df['filename'] = " "
    df.index = range(len(df))
    if len(df[df['names'] == 'Rosa Parks']) == 0:
        print("No Rosa Parks -207!")
        raise SystemExit("BREAK")

    all_links = [i.lower() for i in df['links']]

    bad_files = []
    bad_df_inds = []
    all_files = os.listdir('./HTML/Women/')
    len_files = len(all_files)
    for fNum, fName in enumerate(all_files):
        name = '/' + fName.replace(".html", "").lower()
        print("%i/%i" % (fNum, len_files), end="\r")
        for ilink, link in enumerate(all_links):
            check = link[link.rfind('/'):]
            if name == check:
                df.loc[ilink, 'filename'] = "./HTML/Women/%s" % fName
                break
        else:
    #        print("Bad: ", name)
            bad_files.append(fName)
            bad_df_inds.append(ilink)

    df = df[df['filename'] != ' ']
    if len(df[df['names'] == 'Rosa Parks']) == 0:
        print("No Rosa Parks -226!")
        raise SystemExit("BREAK")

    # Remove any entries with any links with the bad brackets
    bad_bracks = open_list_file("./metadata/Bad_Link_Brackets.list")
    links = []
    for brack in bad_bracks:
        for link in df['links'][df['links'].str.contains(brack)]:
            links.append(link)

            links = list(set(links))
            for link in links:
                df = df[df['links'] != link]
    if len(df[df['names'] == 'Rosa Parks']) == 0:
        print("No Rosa Parks -241!")
        raise SystemExit("BREAK")


    df.to_csv("./metadata/Women_and_Links.csv", index=False)


df = pd.read_csv("./metadata/Women_and_Links.csv")
all_links = rootPage.load_save_all_pages("./HTML/Women/", list(df['links']),
                                         wiki_url, do_soup=False)


new_df = womParse.parse_all_women(df, wiki_url)
new_df.to_csv("./metadata/Women_and_Links.csv", index=False)

df = pd.read_csv("./metadata/Women_and_Links.csv")

if len(df[df['names'] == 'Rosa Parks']) == 0:
    print("No Rosa Parks -257!")
    raise SystemExit("BREAK")


# Remove any entries with any sections that have bad keywords
bad_sections = open_list_file("./metadata/Bad_Sections.list")
bad_sections = list(set([i.lower() for i in bad_sections]))
def set_bad_sections_to_False(section):
    """
    To be applied to df['all_sections'] column and will set any entries
    with bad sections to False
    """
    if type(section) == float: return True
    section = section.lower()
    for sect in bad_sections:
        if sect in section:
            return False
    else:
        return True

mask = df['all_sections'].apply(set_bad_sections_to_False)
df = df[mask]
if len(df[df['names'] == 'Rosa Parks']) == 0:
    print("No Rosa Parks -263!")
    raise SystemExit("BREAK")

# Remove any entries with dodgy things in their info box
all_info_sects = []
all_folds = []
bad_folds = []
bad_links = []
bad_keys = open_list_file('./metadata/Bad_info_box_keys.list')
ignore_keys = open_list_file('./metadata/Good_info_box_keys.list')
for i in range(len(df)):
    fold = df.iloc[i]['profile_path']
    link = df.iloc[i]['links']
    filepath = "%s/all_info.json" % fold
    if os.path.isfile(filepath):
        with open(filepath, "r") as f:
            D = json.load(f)
        if D['info_box'] is False: continue

        keys = [i.lower().strip().strip(':') for i in D['info_box'].keys()]
        if any([j in keys for j in ignore_keys]): continue

        if any([j in keys for j in bad_keys]):
            bad_folds.append(fold)
            bad_links.append(link)
            continue

        name = [i.lower() for i in fold[fold.rfind('/')+1:].split('_')]
        if 'miss' in name:
            bad_folds.append(fold)
            bad_links.append(link)
            continue

        for key in D['info_box']:
            all_info_sects.append(key)
            all_folds.append(fold)

for link in bad_links:
    df = df[df['links'] != link]
if len(df[df['names'] == 'Rosa Parks']) == 0:
    print("No Rosa Parks -303!")
    raise SystemExit("BREAK")

df = df[~df['category'].str.contains('band')]
if len(df[df['names'] == 'Rosa Parks']) == 0:
    print("No Rosa Parks -303!")
    raise SystemExit("BREAK")


df.to_csv("./metadata/Women_and_Links.csv", index=False)

