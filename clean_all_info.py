#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 15:49:40 2019

@author: oem
"""

import json
import os
import re

women_profile_folder = "./Women_Profiles"


def clean_summary(txt):
    """
    Will clean an individual summary text from bits that wouldn't look good in
    the app or that may mess with the database.
    """
    txt = re.sub("\[[0-9]+\]", "", txt)
    lines = txt.split("\n")
    lines = [[word for word in line.split(' ') if word]
             for line in lines]
    lines = [' '.join(words) for words in lines if len(words) > 5]
    txt = '\n\n'.join([i for i in lines if i])
    txt = txt.strip().strip('\n').strip()
    txt = txt.replace('"', "'")
    txt = txt.replace('“', "'")
    txt = txt.replace('”', "'")
    return txt


def clean_all_summaries(women_profile_folder):
    len_files = len(os.listdir(women_profile_folder))-1
    for ifile, fold in enumerate(os.listdir(women_profile_folder)):
        all_info_filepath = "%s/%s/all_info.json" % (women_profile_folder, fold)
        if os.path.isfile(all_info_filepath):
            with open(all_info_filepath, 'r') as f:
                try:
                    D = json.load(f)
                except json.JSONDecodeError:
                    print("Bad Json at: ", all_info_filepath)
                    continue
            if D['summary'] is False: continue
            summary = clean_summary(D['summary'])            
            D['summary'] = summary
            with open(all_info_filepath, 'w') as f:
                json.dump(D, f)
            print("\r%s/%s                    " % (ifile, len_files), end="\r")


def clean_all_sections(women_profile_folder):
    """
    Will do much the same as the clean_all_summaries but applied to the
    contents of all_sections.
    """
    len_files = len(os.listdir(women_profile_folder))-1
    for ifile, fold in enumerate(os.listdir(women_profile_folder)):
        all_info_filepath = "%s/%s/all_info.json" % (women_profile_folder, fold)
        if os.path.isfile(all_info_filepath):
            with open(all_info_filepath, 'r') as f:
                try:
                    D = json.load(f)
                except json.JSONDecodeError:
                    print("Bad Json at: ", all_info_filepath)
                    continue
            all_sects = D['all_sections']
            if all_sects is False: continue
            for key in all_sects:
                D['all_sections'][key] = clean_summary(all_sects[key])
                
            with open(all_info_filepath, 'w') as f:
                json.dump(D, f)
            print("\r%s/%s                    " % (ifile, len_files), end="\r")



print("Cleaning the summaries\n")
clean_all_summaries(women_profile_folder)
           
print("Cleaning all sections\n")
clean_all_sections(women_profile_folder)

