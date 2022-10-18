# for webscraping
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import requests

# for handling dates
from dateutil.parser import parse

# standard libraries
import pandas as pd
import regex as re
import os

# for keeping track of the time
import time
from tqdm import tqdm
from datetime import datetime, timedelta

# from keep_alive import keep_alive
# keep_alive()

lookup_dict = {"South China Morning Post": {"url": "https://www.scmp.com/news/hong-kong",
                                            "homepage": "https://www.scmp.com",
                                           "article_section": ["main", "main-content__first-row"]},
               "Radio Television Hong Kong": {"url": "https://news.rthk.hk/rthk/webpageCache/services/loadModNewsShowSp2List.php?lang=en-GB&cat=8&newsCount=60&dayShiftMode=1&archive_date=",
                                            "homepage": "https://news.rthk.hk/rthk/en",
                                           "article_section": [None, None]},
               "The Standard": {"url": "https://www.thestandard.com.hk/ajax_sections_list.php?sid=4&d_str=&p=1&fc=&trending=0&gettype=section",
                                           "homepage": "https://www.thestandard.com.hk/",
                                           "article_section": [None, None]},
               "Hong Kong Free Press": {"url": "https://hongkongfp.com/category/hong-kong/",
                                           "homepage": "https://hongkongfp.com/",
                                           "article_section": ["div", "entry-wrapper"]},
               "CNN": {"url": "https://edition.cnn.com/data/ocs/container/coverageContainer_A03712C7-CCDD-D04E-E90B-59DD68938925:grid-small/views/containers/common/container-manager.html",
                                           "homepage": "https://edition.cnn.com/",
                                           "article_section": ["div", "zn__containers"]},
               }

# set home data directory path
path = "./data/"

def extract_html_text(text):
    """function to extract and clean up text from a html page"""
    text = text.getText().replace("’", "'").replace("‘", "'").replace('"',"")\
        .replace("|", "").replace("  ", "").replace("Explainer","")\
        .replace("%E2%80%98", "'").replace("%E2%80%99", "'").replace("”", "'")\
        .replace("“", "'").replace("…", " ").replace("-", " ")\
        .encode('utf-8', errors='ignore').decode('utf-8').strip()
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
        text = str(text)
        cleaned_text = text.lower().replace("(", "").replace(")", "")\
            .replace(" published", "").replace(" updated", "").replace("local", "")
        parsed_date = parse(cleaned_text, fuzzy=True).replace(microsecond=0).replace(second=0)
        return parsed_date
    except:
        return False

def look_up_news(lookup_dict, header):
    """scrapes a range of newspaper websites for new articles
    as input one has to provide a dict with information on the newsites to look up
    and as output the function return a dataframe of newspaper articles"""

    # read in old data, if we have none just create an empty list
    try:
        old_data = pd.read_csv("news_data.csv", sep=";")
        old_url_list = old_data["URL"].to_list()
        file_exists = True
    except:
        old_url_list = []
        file_exists = False

    # create empty dict to collect news
    collected_news = {}

    # for all news in the lookup dictionary
    for news_page in tqdm(lookup_dict.keys()):
        # open the page - get the HTML page by making a request
        page = urlopen(Request(url=lookup_dict[news_page]["url"], headers=header)).read()

        # parse content with beautifulsoup
        # we use beautiful soup to search the page for content in an easy way
        searchable_html = BeautifulSoup(page, features="html.parser", )

        # find section of page where articles are stored
        # and get all links of articles there
        link_list = []
        for i in searchable_html.find_all(lookup_dict[news_page]["article_section"][0], \
                                          class_=lookup_dict[news_page]["article_section"][1]):
            for link in i.findAll('a'):
                link_url = clean_up_link(str(link.get('href')))
                if ("article" in link_url or "comment" in link_url or \
                        "news" in link_url) and "video" not in link_url:
                    link_list.append(link_url)

        # if we have not found any links try a different search strategy
        if link_list == []:
            for link in searchable_html.findAll('a'):
                try:
                    link_url = clean_up_link(link.get('href'))
                except:
                    raise ValueError("Could not find link url for link: " + link)
                # do a quality check for the links we find
                # check if they contain news
                link_url = link_url.lower()
                if re.search(r'\d\d\d\d', link_url) != None and \
                                          "photo" not in link_url and \
                                          "app" not in link_url and \
                                          "tel:" not in link_url and \
                                          "video" not in link_url and \
                                          "affiliate" not in link_url:
                    link_list.append(link_url)
                else:
                    pass

        link_list = list(dict.fromkeys(link_list))

        # go through all links found
        for link in tqdm(link_list):

            # skip those link that are already in our collection
            if link in old_url_list:
                continue

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

            # we don't want articles from the archives that's why we skip them
            if "Archive" in article_headline:
                continue

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

            # if we have not found try a different search strategy
            if article_time == None:
                for timestamp in searchable_article.findAll('div', class_="timestamp"):
                    article_time = handle_datetime(extract_html_text(timestamp))
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
                        for time_text in searchable_article.find_all("div", class_=search_string):
                            for timestamp in time_text.find_all("span"):
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
    # convert collected data to dataframe
    news_df = pd.DataFrame.from_dict(collected_news).transpose().reset_index().rename(columns={'index':'URL'})

    # append the existing file or create new one
    if file_exists == True:
        news_df.to_csv("./data/news_data.csv", mode='a', index=False, header=False, sep=";")
    else:
        news_df.to_csv("./data/news_data.csv", index=False, sep=";")

    return "Finished collecting news"

def lookup_weather(url, header):
    """scrapes a range of weather condition for a location (like hongKong)
    as input one has to provide a URL and headers for looking up the page.
    Currently the function is set up to work with weather atlas by Arateco FZ-LLC"""

    #create empty dict to store the data
    weather_dict = {}
    # open the page - get the HTML page by making a request
    page = urlopen(Request(url=url, headers=header)).read()
    # use beautiful soup to search the page for content
    searchable_website = BeautifulSoup(page, 'html.parser')
    page_text= ""
    for text_section in searchable_website.find_all("div", class_= "card border shadow-0 mb-3"):
        page_text += " " + extract_html_text(text_section)

    # find the section where the current measurements are stored
    start_index = re.search("Current condition and temperature\s*Hong Kong, Hong Kong",
                            page_text).span()[1]
    page_text = page_text[start_index:]
    end_index = re.search("UV index: \d*\s*\w", page_text).span()[1]
    page_text = page_text[:end_index]

    # find the current time
    time_index = re.search("\d*:\d* HKT", page_text).span()
    weather_dict["time"] = handle_datetime(str(datetime.now().date()) + " " + page_text[0:time_index[1]])
    page_text = page_text[time_index[1]:]

    # get the current weather condition
    weather_dict["condition"] = page_text[:re.search("\d", page_text).span()[1]-1]
    page_text = page_text[re.search("\d", page_text).span()[1]-1:]

    # now we lookup the following conditions in the website text
    # we find their location then get the value and the unit of measurement if there exists any
    lookup_conditions = ["Wind", "Humidity", "Precipitation", "Visibility", "UV index"]
    for condition in lookup_conditions:
        condition_index = re.search(condition + ": ", page_text).span()[1]
        condition_text = page_text[condition_index:condition_index+re.search("[A-Z]", \
                                   page_text[condition_index:]).span()[1]-1]
        condition_value = re.findall("\d+\.*\d*", condition_text)[0]
        condition_measure = re.findall("[a-z%]+[\\a-z]*", condition_text)
        if condition_measure == []:
            weather_dict[condition] = condition_value
        else:
            weather_dict[condition + " in " + condition_measure[0]] = condition_value

    weather_df = pd.DataFrame(columns=weather_dict.keys())
    weather_df = weather_df.append(weather_dict, ignore_index=True)

    # save data either by appending to file that already exists (if one exists)
    # or by creating new one
    if "weather_data.csv" in os.listdir(path):
        weather_df.to_csv("./data/weather_data.csv", mode='a', header=False, index=False, sep=";")
    else:
        weather_df.to_csv("./data/weather_data.csv", header=True, index=False, sep=";")

def lookup_index(url, header):
    """scrapes the current value of an index.
    As input one has to provide a URL and headers for looking up the page.
    Currently the function is set up to work with Bloomberg"""

    #create empty dict to store the data
    index_dict = {}

    # open the page - get the HTML page by making a request
    page = urlopen(Request(url=url, headers=header)).read()

    # use beautiful soup to search the page for content
    searchable_website = BeautifulSoup(page, 'html.parser')

    # lookup index name and value
    for text_section in searchable_website.find_all("span", class_="priceText__06f600fa3e"):
        index_value = extract_html_text(text_section)
    print(index_value.replace(",", ""))
    for text_section in searchable_website.find_all("div", class_="companyName__1af0080d26"):
        index_name = extract_html_text(text_section)

    index_dict["Datetime"] = datetime.now()
    index_dict["Index Name"] = index_name
    index_dict["Index Value"] = index_value

    index_df = pd.DataFrame(columns=index_dict.keys())
    index_df = index_df.append(index_dict, ignore_index=True)

    # save data either by appending to file that already exists (if one exists)
    # or by creating new one
    if "index_data.csv" in os.listdir(path):
        index_df.to_csv("./data/index_data.csv", mode='a', header=False, index=False, sep=";")
    else:
        index_df.to_csv("./data/index_data.csv", header=True, index=False, sep=";")


def lookup_index_value(url, header):
    pass

header = {'User-Agent': 'Mozilla/5.0'}

#look_up_news(lookup_dict, header)


while True:
    look_up_news(lookup_dict, header)
    lookup_weather("https://www.weather-atlas.com/en/hong-kong/hong-kong#current", header)
    lookup_index("https://www.bloomberg.com/quote/HSI:IND", header)

    # calculate time till next hour
    next_hour = (datetime.now() + timedelta(hours=1))\
       .replace(microsecond=0, second=0, minute=2)
    waiting_time = (next_hour - datetime.now()).seconds

    # sleep for that time
    print("Sucessfully looked up all values now sleeping till next hour for " + str(waiting_time/60) + "minutes")
    time.sleep(waiting_time)

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


