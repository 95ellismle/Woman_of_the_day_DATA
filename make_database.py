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
import re
import chardet
import subprocess

# Need a name, a summary and an info box


def predict_encoding(file_path, n_lines=20):
    """
    Predict a file's encoding using chardet
    """
    # Open the file as binary data
    with open(file_path, 'rb') as f:
        # Join binary lines for specified number of lines
        rawdata = b''.join([f.readline() for _ in range(n_lines)])

    return chardet.detect(rawdata)['encoding']

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
    print("\r%s         " % profile_path[profile_path.rfind('/')+1:], end="\r")
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


def rem_from_dict(D, key):
    bad_keys = [K for K in D if key.lower() in K.lower()]
    for key in bad_keys: D.pop(key)


months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']
def tidy_value(val):
    val = re.sub("\(.*\)", "", val).title()
    val = re.sub("     ", "|||", val)
    return val


def move_image(image_path, name):
    drawableFolder = "/home/oem/AndroidStudioProjects/WomanoftheDay/app/src/main/res/drawable"
    name = name.strip().replace(" ", "_").lower()
    name = re.sub("[^a-z0-9_:]", "", name)
    oldImgName = "./%s.png" % name
#    print('|'+name+'|')
    newImgPath = "%s/%s.png" % (drawableFolder, name)
    if 'carol' in name:
        print(name)
    if os.path.isfile(newImgPath): return

    if os.path.isfile(oldImgName): os.remove(oldImgName)

#    cvtCmd = 'convert "%s" png:%s' % (image_path, oldImgName)
    res = subprocess.Popen(["convert", " -strip", image_path, oldImgName],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stderr = res.stderr.read()
    if len(stderr) == 0:
        res.communicate()
        os.rename(oldImgName, newImgPath)
    else:
        print("cmd: ", ' '.join(["convert", image_path, oldImgName]))
        print(image_path, " -> ", oldImgName)
        print("stderr: ", stderr)
        print("\n\n")
        print("stdout: ", res.stdout.read())
        print("\n\n%s Doesn't Work" % name)
        raise SystemExit("BREAK")
    print("\rMoved %s                                        " % name,
          end="\r")


def get_img_file(profile_path):
    folderpath = "%s/Img/" % (profile_path)
    if not os.path.isdir(folderpath): return False
    imgFiles = [i for i in os.listdir(folderpath) if 'pic_info' not in i]
    if len(imgFiles) != 1:
        if len(imgFiles) == 0:
            return 0
        raise SystemExit(profile_path)
    return os.path.join(folderpath, imgFiles[0])


def get_summary_html(profile_path):
    """
    Will get the summary from the profile_path.
    """
#    print("\r" + profile_path[profile_path.rfind('/')+1:], end="\r")
    filepath = "%s/all_info.json" % (profile_path)
    if not os.path.isfile(filepath): return False
    with open(filepath, 'r') as f:
        D = json.load(f)

    info_box = D['info_box']
    if not info_box: return False
    for key in ('name', 'nationality', 'spouse', 'signature', 'relatives',
                'citizenship', 'partner', 'parent', "\n\n\n"):
        rem_from_dict(info_box, key)
    if any('died' in key.lower() for key in info_box):
        rem_from_dict(info_box, "resting place")

    htmlStr = "<ul>"
    for key, val in info_box.items():
        htmlStr += "<li><strong>%s:</strong> %s</li>" % (key, tidy_value(val))
    htmlStr += "</ul>"
    return htmlStr


def get_info_box_titles(profile_path):
    """
    Will get the titles of the info boxes
    """
#    print("\r" + profile_path[profile_path.rfind('/')+1:], end="\r")
    filepath = "%s/all_info.json" % (profile_path)
    if not os.path.isfile(filepath): return False
#    encoding = predict_encoding(filepath, 200)
    with open(filepath, 'r') as f:
        D = json.load(f)

    info_box = D['info_box']
    if not info_box: return False

    keys = [i.replace(u"\xa0", u" ").lower() for i in info_box.keys() if len(i) < 50 and "\n\n\n" not in i]
    return keys


def has_good_keys(profile_path):
    """
    Will check whether certain keys are in the info box. If not return False.
    """
#    print("\r" + profile_path[profile_path.rfind('/')+1:], end="\r")
    filepath = "%s/all_info.json" % (profile_path)
    if not os.path.isfile(filepath): return False
#    encoding = predict_encoding(filepath, 200)
    with open(filepath, 'r') as f:
        D = json.load(f)

    info_box = D['info_box']
    if not info_box: return False

    good_keys = ['known for', 'occupation', 'also known as', 'notable',
                 'nickname']
    keys = [i.replace(u"\xa0", u" ").lower() for i in info_box.keys()]
    if any([check in key for key in keys for check in good_keys]):
        return True
    return False


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


def get_biog(profile_path):
    """
    Will get up to the first 50 sentences.
    """
    summary = get_summary(profile_path)
    sentences = nltk.sent_tokenize(summary)
    if len(sentences) < 10:
        return False
    return ' '.join(sentences)

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


# First we only want the women with a picture
df = df[df['has_pic'] == True]
df = df.drop("has_pic", axis=1)

# Now the woman needs a summary
df = df[df['has_summary'] ==  True]
df = df.drop("has_summary", axis=1)

### Get the occupations
df['image_path'] = df['profile_path'].apply(get_img_file); df = df[df['image_path'] != False]
df['good_keys'] = df['profile_path'].apply(has_good_keys); df = df[df['good_keys'] == True]
#df['info_box_titles'] = df['profile_path'].apply(get_info_box_titles); df = df[df['info_box_titles'] != False]
df['summary'] = df['profile_path'].apply(get_summary_html); df = df[df['summary'] != False]
df['biography'] = df['profile_path'].apply(get_biog); df = df[df['biography'] != False]
for i in df.index:
    name = df.loc[i, 'names']
    image_path = df.loc[i, 'image_path']
    move_image(image_path, name)


## To test the database I will have to find a better solution later
#mask = [i in insp_wom for i in df['names']]
#insp_df = df[(df['summary_size'] > 200) & (df['summary_size'] < 800)]
#insp_df = df[mask]
#test_df = insp_df[(insp_df['summary_size'] > 200) & (insp_df['summary_size'] < 800)]
#test_df = pd.DataFrame(test_df)
#test_df['quick_summ'] = test_df['summary'].apply(get_quick_summ)
#test_df['biography'] = test_df['summary'].apply(get_biog)
#test_df.index = range(len(test_df))
#
#
# Now create the sqlite3 db
db_filepath = "./Women.db"
if os.path.isfile(db_filepath):  os.remove(db_filepath)
db = sqlite3.connect(db_filepath)

cursor = db.cursor()
cursor.execute("""CREATE TABLE women(id INTEGER PRIMARY KEY AUTOINCREMENT,
                                     name TEXT NOT NULL,
                                     summary TEXT NOT NULL,
                                     biography TEXT NOT NULL);
""")

db.commit()
for i in df.index:
    name, quick_sum, bio = df.loc[i, ["names", "summary", "biography"]]
    insert_cmd = cursor.execute("""INSERT INTO women(name, summary, biography)
                                    VALUES(?,?,?)""", (name, quick_sum, bio) )
    print("\r%s inserted" % name, end="\r")
db.commit()

db.close()
