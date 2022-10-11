# from keep_alive import keep_alive

# for webscraping
from urllib.request import urlopen, Request

# standard libraries
import pandas as pd
import regex as re
from bs4 import BeautifulSoup

# for visuals


# keep_alive()

# while True:
# #enter web scraper
# n = 5

lookup_dict = {"South China Morning Post": {"url": "https://www.scmp.com/news/hong-kong",
                                            "homepage": "https://www.scmp.com",
                                            "article_section": "main-content__first-row"},
               }
collected_news = {}


def look_up_facts(lookup_dict, header):
    for news_page in lookup_dict.keys():

        # open the page
        page = urlopen(Request(url=lookup_dict[news_page]["url"], headers=header)).read()

        # read html and convert it to a string
        html = str(page.decode("utf-8"))

        # use beautiful soup to search the page for content
        searchable_html = BeautifulSoup(html, 'html.parser')

        # this code can be use to find all classes of a webpage
        # we search all tags
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

        # find all articles on the page
        article_section = searchable_html.find_all(
            "div", {"class": lookup_dict[news_page]["article_section"]})

        link_list = []
        for i in article_section:
            for link in i.findAll('a'):
                link_url = link.get('href')
                if "article" in link_url or "comment" in link_url or "news" in link_url:
                    link_list.append(link_url)

        link_list = list(dict.fromkeys(link_list))

        for link in link_list:

            try:
                # open the page
                page = urlopen(Request(url=link, headers=header)).read()
            except:
                link = lookup_dict[news_page]["homepage"] + link
                page = urlopen(Request(url=link, headers=header)).read()

            # read html and convert it to a string
            article = str(page.decode("utf-8"))

            # use beautiful soup to search the page for content
            searchable_article = BeautifulSoup(article, 'html.parser')

            for timestamp in searchable_article.findAll('time'):
                # print(timestamp)
                if timestamp.has_attr('datetime'):
                    article_time = timestamp['datetime']
                break

            for headline in searchable_article.findAll('h1'):
                article_headline = headline.getText().strip()
                break

            search_string = re.compile('.*article.*')
            article_text = ""
            for text in searchable_article.find_all("li", class_=search_string):
                article_text = article_text + text.getText().strip()

            # print(searchable_html.getText())
            # print(link)
            # break
            collected_news[link] = {"datetime": article_time,
                                    "heading": article_headline, "text": article_text, }

        # print(link_list)



header = {'User-Agent': 'Mozilla/5.0'}
look_up_facts(lookup_dict, header)

# convert collected data to dataframe
news_data = pd.DataFrame.from_dict(collected_news).transpose().reset_index().rename(columns={'index':'URL'})
news_data.to_csv("./data/sample_data.csv", index=False)

# time.sleep(3600)
