#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 19:16:21 2019

@author: oem
"""

import pandas as pd
import os
import json
import nltk
import sqlite3

# Need a name, a summary and an info box


def open_list_file(filename):
    """
    Will open a .list file (normally found in metadata folder).
    """
    with open(filename, "r") as f:
        ltxt = [i for i in f.read().split("\n") if i]
    return ltxt


def get_summary(profile_path):
    """
    Will get the summary from the profile_path.
    """
    filepath = "%s/all_info.json" % (profile_path)
    if not os.path.isfile(filepath): return False
    with open(filepath, 'r') as f:
        D = json.load(f)

    summary = D['summary']
    all_sects = D['all_sections']
    if summary is False and all_sects is False: return False

    biography = ""
    if all_sects is not False:
        bio = ""
        bio = [all_sects[key] for key in all_sects
                  if 'biograph' in key.lower()]
        biography += '\n\n'.join(bio)

    if summary is not False:
        biography += D['summary']

    return biography.strip('\n')


def get_len(summary):
    """
    Will get the len in words of the summary in the profile path.
    """
    if summary is not False:
        return len(nltk.word_tokenize(summary))
    return False


def get_quick_summ(summary):
    """
    Will get the first 2 sentences of the summary for the quick summary
    """
    sentences = nltk.sent_tokenize(summary)
    return ' '.join(sentences[:3])


def get_biog(summary):
    """
    Will get up to the first 50 sentences.
    """
    sentences = nltk.sent_tokenize(summary)
    return ' '.join(sentences[:50])

df = pd.read_csv("./metadata/Women_and_Links.csv")
df = df.dropna()
insp_wom = open_list_file("./metadata/Inspirational_Women.list")


# Check if all the women in the inspirational women list are in the main csv
not_in_main_df = []
for i in insp_wom:
    if i not in list(df['names']):
        not_in_main_df.append(i)
if not_in_main_df:
    print("The following women don't seem to appear in the main csv file!")
    print("\n\t*".join(not_in_main_df))
    raise SystemExit("Update the Women_and_Links.csv file to include these")


# Find the women with a summary or a bio
df = df[(df['has_summary'] == True) | (df['all_sections'].str.contains('biog'))]
df['summary'] = df['profile_path'].apply(get_summary)
df = df[df['summary'] != False]
df['summary_size'] = df['summary'].apply(get_len)


# To test the database I will have to find a better solution later
mask = [i in insp_wom for i in df['names']]
insp_df = df[mask]
test_df = insp_df[(insp_df['summary_size'] > 200) & (insp_df['summary_size'] < 800)]
test_df = pd.DataFrame(test_df)
test_df['quick_summ'] = test_df['summary'].apply(get_quick_summ)
test_df['biography'] = test_df['summary'].apply(get_biog)
#test_df.index = range(len(test_df))


# Now create the sqlite3 db
db_filepath = "../../WomanoftheDay/app/src/main/assets/Women.db"
if os.path.isfile(db_filepath):  os.remove(db_filepath)
db = sqlite3.connect(db_filepath)

cursor = db.cursor()
cursor.execute("""CREATE TABLE women(id INTEGER PRIMARY KEY AUTOINCREMENT,
                                     name TEXT NOT NULL,
                                     quick_summ TEXT NOT NULL,
                                     biography TEXT NOT NULL);
""")

db.commit()
for i in test_df.index:
    name, quick_sum, bio = test_df.loc[i, ["names", "quick_summ", "biography"]]
    insert_cmd = cursor.execute("""INSERT INTO women(name, quick_summ, biography)
                                    VALUES(?,?,?)""", (name, quick_sum, bio) )
    print("%s inserted" % name)
db.commit()

db.close()