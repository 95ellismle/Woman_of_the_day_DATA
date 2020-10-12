#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  4 18:38:09 2020


Contains methods/objects relevant to parsing the webpages.

The Parser object is a child of the GetPage object and is just a skeleton
class with some helpful functions for any children parsers (such as the 
                                                            WikiPage object).

WikiPage will parse a wikipedia page. See class docstr for more info.


@author: matt
"""
import myHttp

import os
import unicodedata
import bs4
import pandas as pd


class ImageTag(myHttp.GetImage):
    """
    A class to store the data from an image tag.
    """
    
    def __init__(self, tag):
        if hasattr(tag, "attrs"):
            for i in tag.attrs:
                setattr(self, i, tag.attrs[i])
        
        # Check we do have the src location
        if not hasattr(self, 'src'):
            raise SystemExit("No src attribute for image tag!")
        
        if self.src[:8] != "http://": 
            self.src = self.src.lstrip("/")
            self.src = f"https://{self.src}"
        
        self.filename = self.src[self.src.rfind('/')+1:]
        
        super().__init__(self.src)


class TextObj:
    """
    An object to store the attributes of an bs4.Tag in a more easily accessible
    format.
    
    Input Parameters
    ----------
    Tag : bs4.Tag
        A beautiful soup 4 Tag to get the text from.
    
    
    Parameters
    ----------
    text : str
        The text from the Tag.
    
    links : list<str>
        Any urls that are in the Tag
    
    images : list<ImageTag>
        Any images that are in the tag
    """
    links = []
    text = ""
    images = []
    
    def __init__(self, Tag):
        self.Tag = Tag
        self.text = self._get_text(Tag)
    
    def _get_text(self, Tag):
        """
        Will get the text from a bs4 tag.
        
        This works by recursively digging into the tag until we find a 
        bs4.NavigableString object and returning that (with funny symbols 
                                                       removed).

        Parameters
        ----------
        tag : bs4.Tag
            The tag with text you want to grab.

        Returns
        -------
        None

        """
        s = ""
        if hasattr(Tag, 'name'):
            name = Tag.name
            if name == "img": self.images.append(ImageTag(Tag))
            elif name == "a": s += self._parse_anchor(Tag)
            
        if hasattr(Tag, "children"):
            for new_tag in Tag.children:
                s += unicodedata.normalize("NFKD", self._get_text(new_tag))
                    
        elif isinstance(Tag, (bs4.NavigableString, str)):
            s += Tag
            
        elif (type(Tag) == bs4.Tag):
            raise SystemExit("Please look again at handling tags!")
            if Tag.name == 'br':  s += "\n"
        
        else:
            raise SystemExit("Don't know how to parse text from:" + 
                             "\n\t tag = " + f"{Tag}"+
                             "\n\t tag type = " + f"{type(Tag)}"   )
        
        return s
    
    def _parse_anchor(self, Tag):
        """
        Will parse an anchor tag and add the details to the links list
        """
        if hasattr(Tag, "attrs") and 'href' in Tag.attrs:
            name = Tag.get_text()
            print(name)
            
        

class Parser(myHttp.GetPage):
    """
    A general parser type webpage parsing.
    
    The workflow of this class is:
        1) get the webpage and soupify it
        2) call a parse function
        3) save the data -including the webpage
    """
    parsedData = {}
    def __init__(self,  url, must_contain=[], soup=False, throw_error=False, 
                 savedir="auto"):
        """
        Init Function.
        
        
        Parameters
        ----------        
        url : str
            The url of the webpage.
        
        must_contain : list, optional
             Any strings the website must have. The default is [].

        soup : boolean, optional
            Whether to parse the html into a bs4 object. The default is False.
            
        throw_error : boolean, optional
            Whether to throw an error if the page can't be found or silenty 
            handle it. The default is False.


        Returns
        -------
        None.

        """

        super().__init__(url, must_contain, soup, throw_error)
        
        # Create the savedirectory if not given
        if savedir == "auto":
            if (splitter := self.url.split('/')):
                # If it is a file
                if os.path.isfile(self.url):
                    self.save_dir = '/'.join(splitter[:-1])
                
                # If it is 
                elif self.isURL:
                    self.save_dir = f"./{splitter[-1]}"
        
        elif type(savedir) == str:
            self.save_dir = savedir
        
        self._parse()
        
        if savedir is False:
            self._save()
    
    def _parse(self):
        """
        The parser function. Override this in derived classes.
        """
    
    def _save(self):
        """
        Will save the page data.
        
        A folder is created with the last part of the url. Then all data that 
        has been parsed in saved.

        Returns
        -------
        None.

        """     
        self.save_page(f"{self.save_dir}/Wiki.html")

    def _get_children_dict(self, Tag):
        """
        Will return a dictionary with the children of a bs4.Tag

        Parameters
        ----------
        Tag : bs4.Tag
            The tag that the children should be parsed from.

        Returns
        -------
        dict:
            The children dictionary. keys = tag.name
                                     values = [tag1, tag2, ...]

        """
        children = {}
        for child in Tag.children:
            if hasattr(child, "name") and child.name is not None:
                children.setdefault(child.name, []).append(child)
        
        return children

    
    def _parse_general_tbody(self, tbdySoup):
        """
        Will parse a general tbody object and get the th, td etc..

        Parameters
        ----------
        tbdySoup: bs4.soup
            The soup object that contains the tbody.

        Returns
        -------
        dictionary:
            The table data as a dictionary.      

        """
        children = self._get_children_dict(tbdySoup)
        
        # Find the table rows
        if 'tr' in children:
            names = None
            tables = [{}]
            table_count, th_init = 0, False
            table = tables[0]
            
            # Iterate over the table rows
            for td in children['tr']:
                # Wrap this up n a function
                trChildren = self._get_children_dict(td)
                
                # If we have a table head then create a new table
                if 'th' in trChildren:
                    if th_init is False: th_init == True
                    else:
                        table_count += 1
                        tables.append({})
                        table = tables[table_count]
                    
                    # Create the table
                    names = [self._get_text(tag).strip("\n ") for tag in trChildren['th']]
                    for name in names:
                        table.setdefault(name, [])
                    
                    img_data = {i: [] for i in table}

                # If we have some table data then try populating the table in
                #  each of the headers. If there are too many entries create a
                #  new header.
                elif 'td' in trChildren:
                    # Wrap this up in a function.
                    row_data = [self._get_text(i, return_img=True)
                                for i in trChildren['td']]
                    tkeys = list(table.keys())

                    # Add some new entries in the table -if required
                    if len(table) != len(row_data):
                        for i in range(len(row_data) - len(table)):
                            new_nameO, new_name, count = "untitled", "untitled", 0
                            while (new_name in table):
                                new_name = f"{new_nameO}_{count}"
                                count += 1
                            
                            if len(table):
                                table.setdefault(new_name,
                                                 [None]*len(table[tkeys[0]]))
                                img_data.setdefault(new_name,
                                                    [None]*len(table[tkeys[0]]))
                            else:
                                table[new_name] = []
                                img_data[new_name] = []
                                
                            names.append(new_name)
                    tkeys = list(table.keys())
                    
                    for i, (txt, imgs) in enumerate(row_data):
                        table[tkeys[i]].append(txt.strip("\n "))
                        img_data[tkeys[i]].append(imgs)


    def _parse_general_table(self, tableSoup):
        """
        Will parse a general table object and get the th, td etc..

        Parameters
        ----------
        tableSoup : bs4.soup
            The soup object that contains the table.

        Returns
        -------
        dictionary:
            The table data as a dictionary.      

        """
        children = self._get_children_dict(tableSoup)
        
        # Loop over the children and call the relevant parser
        if 'tbody' in children:
            for tbl in children['tbody']:
                self._parse_general_tbody(tbl)
                    
        else:
            raise SystemExit("Please ammend the table parser to include table tags without <tbody>.")

class WikiPage(Parser):
    """
    Will parse a wiki page.
    
    This works by:
        * Finding any tables and restructuring the data into dataframes. This
            data is stored in a dictionary named self.table_data.
        * Finding any paragraphs and the section title. This text is then
            stored in a dictionary named self.paragraph_data.
    """
    def __init__(self, url, must_contain=[], soup=False, throw_error=False, 
                 savedir="auto"):
        super().__init__(url=url, must_contain=must_contain,
                         soup=soup, throw_error=throw_error,
                         savedir=savedir)

    def _parse(self):
        """
        Override of parent's parse function.
        """
        # self.__parse_tables()
    
    def __parse_para(self):
        """
        Parse any paragraphs of text and get a section title.
        """
    
    def __parse_tables(self):
        """
        Will find tables on a wiki page and parse them into dictionaries.

        Returns
        -------
        None.

        """
        tables = self.soup.findAll("table")
        if not tables: return
        
        # Loop over the table objects
        self.table_data = {}
        for tbl in tables:
            attrs = tbl.attrs
            if "infobox" in attrs.get('class', ""):
                self.table_data['infobox'] = self.__parse_infobox(tbl)
            else:
                self._parse_general_table(tbl)
                break

        
    def __parse_infobox(self, tableSoup):
        """
        Will parse an infobox table from a wiki page (the box in the top left).

        Parameters
        ----------
        tableSoup : bs4.soup
            The soup object that contains the infobox table.

        Returns
        -------
        dictionary:
            The table data as a dictionary.
        
        """
        data = {}
        name = ""
        if hasattr(tableSoup, 'th'):
            name = self._get_text(tableSoup.th).strip("\n ")
        else:
            if hasattr(self.soup, "title"):
                name = self._get_text(self.soup.title).strip("\n ")
                name = name.replace("- Wikipedia", "").strip()
        data['page'] = [name]
        
        for row in tableSoup.findAll("tr"):
            childrenTypes = tuple(map(lambda x: x.name, row))
            if childrenTypes == ('th', 'td'):
                children = tuple(row.children)
                header = children[0].text
                data[header] = [self._get_text(children[1]).strip("\n ")]
        
        return data
                
        
    # def __parse_tbody(self):
    #     """
    #     Will parse the table body from a table 
    #     """
        
        
        
        
        
    
W = WikiPage("./100_Women_(BBC)/Wiki.html")
elm = W.soup.findAll('a')[4].parent
TextObj(elm)
# W = WikiPage("./Cape_Feare/Wiki.html")
