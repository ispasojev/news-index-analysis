# for webscraping
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import requests

# for handling dates
from dateutil.parser import parse

# standard libraries
import pandas as pd
import regex as re

# for keeping track of the time
import time
from tqdm import tqdm

# from keep_alive import keep_alive
# keep_alive()

# while True:
# #enter web scraper

lookup_dict = {"South China Morning Post": {"url": "https://www.scmp.com/news/hong-kong",
                                            "homepage": "https://www.scmp.com",
                                           "article_section": "main-content__first-row"},
               "Radio Television Hong Kong": {"url": "https://news.rthk.hk/rthk/webpageCache/services/loadModNewsShowSp2List.php?lang=en-GB&cat=8&newsCount=60&dayShiftMode=1&archive_date=",
                                            "homepage": "https://news.rthk.hk/rthk/en",
                                            "article_section": "No suitable section/class"},
               #"The Standard": {"url": "https://www.thestandard.com.hk/ajax_sections_list.php?sid=4&d_str=&p=1&fc=&trending=0&gettype=section",
                          #                 "homepage": "https://www.thestandard.com",
                                #           "article_section": "No suitable section/class"},
               }
collected_news = {}

def extract_html_text(text):
    """function to extract and clean up text from a html page"""
    text = text.getText().replace("’", "'").replace("‘", "'").replace('"',"")\
        .replace("|", "").replace("  ", "").replace("Explainer","")\
        .replace("%E2%80%98", "'").replace("%E2%80%99", "'").strip()
    return text

def clean_up_link(text):
    """function to remove characters from links that could become problematic
    in the sense that you could not open the link with them for example"""
    text = str(text).replace("‘", "/'").replace("’", "/'")
    return text

def handle_datetime(text):
    """The following function has two purposes:  1) checking if a string contains a datetime
    object and 2) return this object if that is the case"""
    try:
        cleaned_text = text.replace("(", "").replace(")", "").replace("Local", "").replace(" HKT", "")
        parsed_date = parse(cleaned_text, fuzzy=False)
        return parsed_date
    except:
        return False

def look_up_news(lookup_dict, header):
    """scrapes a range of newspaper websites for new articles
    as input one has to provide a dict with information on the newsites to look up
    and as output the function return a dataframe of newspaper articles"""
    for news_page in tqdm(lookup_dict.keys()):

        # open the page - get the HTML page by making a request
        page = urlopen(Request(url=lookup_dict[news_page]["url"], headers=header)).read()

        # parse content with beautifulsoup
        # we use beautiful soup to search the page for content in an easy way
        searchable_html = BeautifulSoup(page, features="html.parser", )

        # find section of page where articles are stored
        # and get all links of articles there
        link_list = []
        for i in searchable_html.find_all("div", class_=lookup_dict[news_page]["article_section"]):
            for link in i.findAll('a'):
                link_url = clean_up_link(str(link.get('href')))
                if "article" in link_url or "comment" in link_url or "news" in link_url:
                    link_list.append(link_url)

        # if we have not found any links try a different search strategy
        if link_list == []:
            for link in searchable_html.findAll('a'):
                try:
                    link_url = clean_up_link(link.get('href'))
                except:
                    raise ValueEroor("Could not find link url for link: " + link)
                # do a quality check for the links we find
                # check if they contain news
                if re.search(r'\d\d\d\d', link_url) != None and \
                                          "photo" not in link_url and \
                                          "app" not in link_url:
                    link_list.append(link_url)
                else:
                    pass

        link_list = list(dict.fromkeys(link_list))

        # go through all links found
        for link in tqdm(link_list):
            # see if we can open the page if not we will add the main page to the URL
            try:
                page = urlopen(Request(url=link, headers=header)).read()
            except:
                try:
                    page = urlopen(Request(url=lookup_dict[news_page]["homepage"] + str(link), headers=header)).read()
                    link = lookup_dict[news_page]["homepage"] + str(link)
                #if we still cannot open the link we throw an error
                except:
                    print("Could not open " + link)

            # use beautiful soup to search the page for content
            searchable_article = BeautifulSoup(page, 'html.parser')

            # trying to the headline of the article
            article_headline = ""
            for headline in searchable_article.findAll('h1'):
                article_headline = article_headline + " " + extract_html_text(headline)
            # if we have not found it that way - try it another way
            if article_headline == "":
                for headline in searchable_article.findAll('h2'):
                    article_headline = article_headline + " " + extract_html_text(headline)
                # if we have not found it that way - try it another way
                if article_headline == "":
                    # if we still have not found anything raise an error
                    if article_headline == "":
                        print("No headline found for URL " + link)
                        continue
                        #raise ValueError("No headline found for URL " + link)

            # trying to the text of the article
            article_text = ""
            search_string = re.compile('.*article.*')
            for text in searchable_article.find_all("li", class_=search_string):
                article_text = article_text + " " + extract_html_text(text)
            # if we have not found it that way - try it another way
            if article_text == "":
                search_string = re.compile('.*Text.*')
                for text in searchable_article.find_all("div", class_=search_string):
                    article_text = article_text + " " + extract_html_text(text)
                # if we have not found it that way - try it another way
                if article_text == "":
                    for text in searchable_article.find_all("p"):
                        article_text = article_text + " " + extract_html_text(text)
                    # if we still have not found anything raise an error
                    if article_text == "":
                        raise ValueError("No text found for URL " + link)

            # trying to extract the date when the article was published
            article_time = None
            for timestamp in searchable_article.findAll('time'):
                if timestamp.has_attr('datetime'):
                    article_time = handle_datetime(timestamp['datetime'])

                break
            if article_time == None:
                search_string = re.compile('.*createddate.*')
                for timestamp in searchable_article.find_all("div", class_=search_string):
                    extracted_time = handle_datetime(extract_html_text(timestamp))
                    if extracted_time != False:
                        article_time = extracted_time
                # if we still have not found try a different search strategy
                if article_time == None:
                    search_string = re.compile('.*heading.*')
                    for header in searchable_article.find_all("div", class_=search_string):
                        for timestamp in header.find_all("span"):
                            extracted_time = handle_datetime(extract_html_text(timestamp))
                            if extracted_time != False:
                                article_time = extracted_time
                        # if we still have not found anything raise an error
                        if article_time == None:
                            raise ValueError("No time found for URL " + link)

            collected_news[link] = {"datetime": article_time,
                                    "heading": article_headline,
                                    "text": article_text,
                                    "newssite": news_page}

        # print(link_list)



header = {'User-Agent': 'Mozilla/5.0'}
look_up_news(lookup_dict, header)

# convert collected data to dataframe
news_data = pd.DataFrame.from_dict(collected_news).transpose().reset_index().rename(columns={'index':'URL'})
news_data.to_csv("./data/sample_data.csv", index=False, sep=";")

# time.sleep(3600)



# appendix

# this code can be use to find all classes of a webpage
# useful if we do not yet know the structure of the website
# we search all tags
# page = requests.get(lookup_dict[news_page]["url"])
# soup = BeautifulSoup(page.content, 'html.parser')
# for tag in {tag.name for tag in searchable_html.find_all()}:
# for i in searchable_html.find_all( tag ):
# if tag has attribute of class
# if i.has_attr( "class" ):
# if len( i['class'] ) != 0:
# class_list.append(i['class'][0])
# for i in class_list:
#   if "time" in i :
#      print(i)
# print(class_list)


