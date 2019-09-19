import bs4
import pandas as pd
import json
import requests
import shutil
import time
import os
import numpy as np
import re

import myHttp


def parse_woman(df_entry, wiki_url):
    """
    Will parse the woman's page to get vital info.
    """
    fName = df_entry['filename']
    with open(fName, "r") as f:
        txt = f.read()
    name = df_entry['names']

    soup = bs4.BeautifulSoup(txt, 'lxml')

    all_info = {}
    return_code = '0'

    # Get the picture and the credit etc...
    pic_info = get_pic_info(soup, wiki_url)
    if pic_info == False:
        print("Couldn't get a pic. Name = %s" % name)
        return_code += ' 1'
    else:
        print(pic_info['url'])
        download_pic(pic_info['url'], name)
        save_pic_info(pic_info, name)
    all_info['pic'] = pic_info

    # Get the info in the table at the side
    info_box = parse_info_box(soup)
    if info_box is False:
        print("Couldn't get the info box. Name = %s" % name)
        return_code += ' 1'
    else:
        info_box['Name'] = name.title()
    all_info['info_box'] = info_box

    # Get the first paragraph (the summary)
    summary = get_summary(soup)
    if summary is False:
        print("Couldn't get summary. Name = %s" % name)
        return_code += ' 1'
    all_info['summary'] = summary

    # Get all the sections in the page
    all_sections = get_all_sections(soup)
    if all_sections is False:
        print("Couldn't find all the sections on wiki page. Name = %s" % name)
        return_code += ' 1'
    all_info['all_sections'] = all_sections

    all_info['err_code'] = return_code

    # Get the impact the woman had on the world
    impact_factor = get_importance(soup, name, all_info)
    all_info['impact_factor'] = impact_factor

    return all_info


def get_pic_info_credit(link):
    """
    Will get the source and general info of the picture from wiki
    """
    img_name = link[link.rfind('/') + 1:]

    filename = "./HTML/Women_Img/%s" % img_name
    if '.html' != filename[-5:]:
        filename = filename[:filename.rfind('.')+1] + 'html'
    soup = myHttp.get_page_soup(link, filename)
    if soup is False: return False
    info_table = soup.findAll("table", {'class': "fileinfotpl-type-information toccolours vevent mw-content-ltr"})
    if len(info_table) != 1:
        print("Found an incorrect number of info tables. I found %i." % len(info_table))
        return False
    pic_info = {}
    for tr in info_table[0].find_all("tr"):
        td = tr.find_all("td")
        if len(td) == 2:
            if td[0].attrs.get("class") == ['fileinfo-paramfield']:
                for span in td[0].find_all('span'):
                    span.replace_with("")
                pic_info[td[0].text] = td[1].text.strip("\n").replace("English:", "").strip()
    return pic_info


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


def save_pic_info(pic_info, name):
    """
    Will save the pic_info as a json file.
    """
    folderpath = make_folderpath(name, "Img").replace(" ", "_")
    with open(folderpath + "/pic_info.json", 'w') as f:
        json.dump(pic_info, f)


def download_pic(pic_url, name):
    """
    Will download the picture for the woman (if the file doesn't exist) and
    save it.
    """
    name = name.replace(" ", "_")
    ext = pic_url[pic_url.rfind('.')+1:]
    folderpath = make_folderpath(name, "Img")
    filepath = "%s/%s.%s" % (folderpath, name, ext)
    filepath = filepath.replace(" ", "_")

    if not os.path.isfile(filepath):
        print("\rDownloading Pic for %s\n" % name)
        try:
            r = requests.get(pic_url, stream=True)
        except:
            print("Can't download %s" % pic_url)
            time.sleep(2)
            return False
        if r.status_code == 200:
            with open(filepath, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        time.sleep(0.2)


def get_pic_info(soup, wiki_url):
    """
    Will get the picture from the infobox on a wiki page
    """
    title = soup.title.text

    info_box = get_info_box(soup)
    if info_box is False:
        return False

    pic_info = False
    found_img = False
    for td in info_box.find_all('td'):
        if len(td.find_all("img")) > 0:
            if 'signature' in str(td).lower():
                continue
            img = td.find_all("img")
            if len(img) != 1:
                continue
            found_img = True

            div = td.find('div')
            if div is not None:
                caption = div.text
            else:
                continue

            src_link = img[0].attrs['src']
            img_link = "%s//%s" % ("https:", src_link)
            a = td.find("a")
            if a is None: continue
            attrs = a.attrs
            link = wiki_url + attrs['href']
            pic_info = get_pic_info_credit(link)
            if pic_info is False:
                print("Can't find any pic_info")
                continue
            pic_info['caption'] = caption
            pic_info['url'] = img_link

    if found_img is False:
        print("Can't find image for %s" % title)

    return pic_info


def get_info_box(soup):
    """
    Will get the info box that holds some nice structured info on the wiki page
    """
    title = soup.title.text

    tables = []
    all_classes = []
    for table in soup.find_all("table"):
        attrs = table.attrs
        if attrs.get('class') is not None:
            all_classes.append(attrs['class'])
            classes_to_find = ('infobox', 'vcard')
            if all(j in attrs['class'] for j in classes_to_find):
                tables.append(table)
    if len(tables) == 1:
        return tables[0]
    else:
        print("Can't find 1 info box -found %i" % len(tables))
        print("title = %s" % title)
#        print("All the classes of the tables:\n\t*%s" % "\n\t*".join(all_classes))
        return False


def parse_info_box(soup):
    """
    Will parse the information from the info_box table and return a dictionary.
    """
    info_box = get_info_box(soup)
    if info_box is False:
        print("Can't find info box!")
        return False

    info_box_parsed = {}
    for tr in info_box.find_all("tr"):
        th = tr.find("th")
        if th is None:
            continue
        td = tr.find('td')
        if td is None:
            continue
        tags = ['span', 'li', 'style']
        for tag in tags:
            for elm in td.find_all(tag):
                elm.replace_with(" " + elm.text + " ")
        text_str = []
        for child in td.children:
            if isinstance(child, (bs4.NavigableString, bs4.element.NavigableString,
                                  bs4.Comment, bs4.element.Comment)):
                text_str.append(str(child) + " ")
#                print(child)
            else:
                text_str.append(child.text + " ")
        info = ' '.join(text_str).replace("  ", " ").strip()
        info_box_parsed[th.text.strip()] = info

    if len(info_box_parsed) == 0:
        title = soup.title.text
        print("Can't parse the info box! Title = %s" % (title))

    return info_box_parsed


def find_toc_parent_div(curr_div, parent_div):
    """
    Will find the div that is highest in the hierachy that still has toc in its
    class.
    """
    attrs = parent_div.attrs
    if attrs is None: return False
    att_class = attrs.get("class")
    if att_class is None: return False

    parent_is_toc = False
    for i in att_class:
        if 'toc' in i:
            parent_is_toc = True

    if parent_is_toc:
        return find_toc_parent_div(curr_div.parent, parent_div.parent)
    else:
        return curr_div


def get_summary(soup):
    """
    Will get the summary from the wiki page.
    """
    title = soup.title.text
    contents_div = soup.find("div", {'id': 'toc'})
    if contents_div is None:
        contents_div = soup.find("h2")
    if contents_div is None: return False
    contents_div = find_toc_parent_div(contents_div, contents_div.parent)
    if contents_div is False: return False

    summary = ""
    bad_tags = ['style']
    for elm in list(contents_div.previous_siblings)[-1::-1]:
        if elm.name == 'p':
            for tag in bad_tags:
                for bad_tag in elm.find_all(tag):
                    bad_tag.replace_with("")
            summary += elm.text + "\n"
    if summary:
        return summary
    else:
        print("Couldn't find summary for %s" % title)
        print("Summary = %s" % summary)
        return False


def get_all_sections(soup):
    """
    Will return a dictionary with all the sections and their text from the wiki
    page.
    """
    sections = {}
    for header in soup.findAll("h2"):
        title = re.sub("\[.*\]", "", header.text)
        text = ""
        bad_tags = ['style']
        for sib in header.next_siblings:
            if sib.name == 'h2':
                break
            bad_tags = ['style']

            if sib.name == 'h3':
                sub_title = re.sub("\[.*\]", "", sib.text)
                text += sub_title + " (subTitle)\n"
            elif sib.name == 'p':
                for tag in bad_tags:
                    for bad_tag in sib.find_all(tag):
                        bad_tag.replace_with("")
                text += sib.text + "\n"
        sections[title] = text

    return sections


def get_importance(soup, name, all_info):
    """
    Will determine the impact the woman had on the world by getting the number
    of search results and the length of the wiki article and whether my code
    could scrape their wiki page.
    """
    search_query = "https://www.ecosia.org/search?q=%s" % '+'.join(name.split(' '))
    return_sum = sum([int(i) for i in all_info['err_code'].split(' ') if i])
    if return_sum > 2:
        return 0

    len_file = len(soup.text.split('\n'))
    impact_1 = 2 - (275/len_file) ** 2
    if impact_1 < 0: impact_1 = 0
    if len_file < 275:
        return 0

    search_filename = "./HTML/Search_Results/%s.html" % name
    if not os.path.isfile(search_filename):
        print("Downloading new ecosia page")
        page = myHttp.GetPage(search_query, must_contain=[name])
        soup = page.soup
        myHttp.save_html_page(soup, search_filename)
        time.sleep(0.5)
    else:
        soup = myHttp.open_html_page(search_filename)

    span = soup.find("span", {'class': 'result-count'})
    if span is not None:
        search_results = span.text.replace("\n", "").replace('results', '')
        search_results = search_results.strip().replace(",", "")
        search_results = int(search_results)
    else:
        search_results = -1

    impact_2 = 1 - (300000/search_results)
    if impact_2 < 0: impact_2 = 0

    return (impact_1 + impact_2) / 2.



def save_all_info(all_info, name):
    """
    Will save the info gathered from the wikipedia page
    """
    folderpath = make_folderpath(name)
    with open("%s/all_info.json" % folderpath, 'w') as f:
        json.dump(all_info, f)

def load_numpy(file, default=[]):
    """
    Will load a numpy file or return the default
    """
    if os.path.isfile(file):
        data = np.load(file)
    else:
        data = []
    return data


def parse_all_women(df, wiki_url):
    """
    Will parse all the pages of the women in the database and save their
    details in sensible places.
    """
    parsed_filename = "./metadata/Parsed_Women.npy"
    parsed_women = list(load_numpy(parsed_filename))
    df['impact_factor'] = 0

    for i in range(len(df)):
        link = df.loc[i, 'links']
        name = df.loc[i, 'names']

        if link not in parsed_women:
            all_info = parse_woman(df.loc[i], wiki_url)

            df.loc[i, 'impact_factor'] = all_info['impact_factor']
            save_all_info(all_info, name)
            parsed_women.append(link)
            print("Impact Factor = ", all_info['impact_factor'])

        print("\rDone %s (%i/%i)                                                 " % (name, i, len(df)), end="\r")

    np.save(parsed_filename, parsed_women)

    df = add_profile_path(df)
    df = add_has_pic(df)
    df = add_all_sections(df)
    df = add_has_summary(df)
    df = add_has_info_box(df)
    df = add_has_info_box(df)

    return df


def add_has_pic(df):
    """
    Adds a column -has_pic to the dataframe letting the user know whether there
    is a picture available for each person
    """
    def has_pic(folderpath):
        if os.path.isdir(folderpath + '/Img'):
            return True
        else:
            return False

    df['has_pic'] = df['profile_path']
    df['has_pic'] = df['has_pic'].apply(has_pic)
    return df


def add_profile_path(df):
    """
    Add a pointer column to the dataframe pointing to the Women_Profile folder
    """
    df['profile_path'] = df['names']
    df['profile_path'] = df['profile_path'].apply(make_folderpath)
    return df


def add_all_sections(df):
    """
    Will add the all_sections column to the df
    """
    def has_all_sections(profile_path):
        filepath = profile_path + '/all_info.json'
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                D = json.load(f)
                if D.get("all_sections") is not False:
                    sections = [i.lower().strip() for i in list(D['all_sections'].keys())]
                    bad_sections = ['contents', 'navigation menu']
                    for sect in bad_sections:
                        if sect in sections: sections.remove(sect)
                    sections = ' | '.join(sections).lower()
                    return sections
        return False

    df['all_sections'] = df['profile_path']
    df['all_sections'] = df['all_sections'].apply(has_all_sections)
    return df


def add_has_summary(df):
    """
    Will add the all_sections column to the df
    """
    def has_summary(profile_path):
        filepath = profile_path + '/all_info.json'
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                D = json.load(f)
                if D.get("summary") is not False:
                    return True
        return False

    df['has_summary'] = df['profile_path']
    df['has_summary'] = df['has_summary'].apply(has_summary)
    return df


def add_has_info_box(df):
    """
    Will add the all_sections column to the df
    """
    def has_info_box(profile_path):
        filepath = profile_path + '/all_info.json'
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                D = json.load(f)
                if D.get("info_box") is not False:
                    return True
        return False

    df['has_info_box'] = df['profile_path']
    df['has_info_box'] = df['has_info_box'].apply(has_info_box)
    return df


#df = pd.read_csv("./metadata/Women_and_Links.csv")
#wiki_url = "https://en.wikipedia.org"
#new_df = parse_all_women(df, wiki_url)
#new_df.to_csv("./metadata/Women_and_Links.csv", index=False)