import time
import configparser
import logging
import os
import re
import sys
import time
import datetime

import pandas as pd
import urllib3
import xlsxwriter

import requests
from bs4 import BeautifulSoup, Comment
from requests.exceptions import ConnectionError
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

# Add custom user-agent to prevent blocking
#from selenium.webdriver.chrome.options import Options
#from fake_useragent import UserAgent

#ua = UserAgent()
#chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument(f'--user-agent={ua.random}')


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



def first_query_page():
    #Add a CLI to input the date range of the crawler (also add the date auto detection --> because max query per session is 500)


    #Access the main search page of the law precedent system
    #driver download: https://googlechromelabs.github.io/chrome-for-testing/
    #In the latest version of Selenium, webdriver is no longer needed to be downloaded
    #https://stackoverflow.com/questions/76550506/typeerror-webdriver-init-got-an-unexpected-keyword-argument-executable-p
    #driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome()
    url = "https://judgment.judicial.gov.tw/FJUD/Default_AD.aspx"
    driver.get(url)

    #Find the elements and simulate the clicks

    #Type of precendent
    #find_element function is changed
    #https://stackoverflow.com/questions/72773206/selenium-python-attributeerror-webdriver-object-has-no-attribute-find-el
    
    #checkbox switch variable for law type (刑事, 民事 or others)
    #law_type = "//*[@id='vtype_M']/input"
    law_type = "//*[@id='vtype_V']/input"
    driver.find_element(By.XPATH, law_type).click()
    #Date range start
    year_field1 = driver.find_element("name", "dy1")
    year_field1.send_keys(113)
    month_field1 = driver.find_element("name", "dm1")
    month_field1.send_keys(1)
    day_field1 = driver.find_element("name", "dd1")
    day_field1.send_keys(1)
    #Date range end
    year_field2 = driver.find_element("name", "dy2")
    year_field2.send_keys(113)
    month_field2 = driver.find_element("name", "dm2")
    month_field2.send_keys(1)
    day_field2 = driver.find_element("name", "dd2")
    day_field2.send_keys(2)
    #Select the court
    driver.find_element(By.XPATH, "//*[@id='jud_court']/option[22]").click()
    #Click the search button
    driver.find_element("name", "ctl00$cp_content$btnQry").click()


    #Frame switch will still work after page switching, no need to be in the for loop
    driver.switch_to.frame("iframe-data")

    
    # Definte the article_URLs variable here to avoid being reset in loop...
    article_URLs = []
    # Continue with this part for the next page loop (in total max 25 pages per search session)
    for i in range(24):
        if i == 0:
            pass
        elif len(driver.find_elements("id", "hlNext")) == 0:
            break
        else:
            driver.find_element("id", "hlNext").click()


        # Fetch all the URLs of the query result
        # Should use a for loop to automate saving all the URLs for the individual data page

        #Switch frame (Very important for dynamic load with iframes or others)
        #https://ithelp.ithome.com.tw/articles/10269242
        #https://selenium-python.readthedocs.io/api.html
        #driver.switch_to.frame("iframe-data")
        
        
        # Wait for the page to load
        #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'hlTitle')))
        #WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'hlTitle')))
        time.sleep(1)

        # Extract the page source
        page_source = driver.page_source
        #page_source = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")

        # Parse the page source with BeautifulSoup
        source_soup = BeautifulSoup(page_source, 'html.parser')
        page_content = source_soup
        #Print test
        #print(page_content)

        #Conditioned article URL fetch (Some URL are None)
        for node in page_content.find_all("a", id="hlTitle"):
            if node.get("href") is not None:
                article_URLs.append(f'https://judgment.judicial.gov.tw/FJUD/{node.get("href")}')
            else:
                pass
        
        #
        print("Cuurent page: " + str(i+1) + "/" + "25")
        ## print test
        #print(article_URLs)
        #print(len(article_URLs))
    
    # Print test
    print(article_URLs)
    return article_URLs


# Crawling the individual page
def crawl_individual_page(content):
    jud_div=content.find('div', class_='int-table col-xs-8', id='jud')
    jud_div_text = jud_div.get_text(separator='', strip=True)
    # raw-stripped strings method:
    # jud_div_text = [text for text in jud_div.stripped_strings]

    #Remove dirty spaces
    jud_div_text=jud_div_text.replace(' ', '').replace(' ', '').replace('　', '')
    #print(jud_div_text)
    return jud_div_text



# Making soup
def get_bs4_content(url):
    res = requests.get(url, verify=False)
    soup = BeautifulSoup(res.text, "html.parser")
    return soup



#Main function

#Calling the single page crawler
#crawl_individual_page(get_bs4_content(first_query_page()[0]))



# Save the first query article URLs result
Article_URLs = first_query_page()
#print(Article_URLs[0])
print("Article_URLs transfer finished")


# Old functions
'''
# Initiate the bs4 raw contents container array
bs4_raw_contents = []
# Populating the bs4_raw_contents array
for i in range(len(Article_URLs)):
    bs4_raw_contents.append(get_bs4_content(Article_URLs[i]))
    print("I am running!\nProgress:" + str(i) +"/" + str(len(Article_URLs)))
print(bs4_raw_contents[0])
print("bs4_raw_contents populate finished")
# Crawl all the contents
# Initiate the final crawled text array
crawled_text = []
for i in range(len(bs4_raw_contents)):
    crawled_text.append(crawl_individual_page(bs4_raw_contents[i]))
'''


# Writing the crawled_text to txt file
# Create a new txt file
#https://www.w3schools.com/python/python_file_write.asp
timestamp = str(datetime.datetime.now()).replace(' ','_').replace(':','').replace('.','_')
file_name = "Crawled_text_"+timestamp+".txt"
f = open(file_name, "a", encoding="utf-8")


# joint function
# Forget about the array, changing to file output
#crawled_text = []
for i in range(len(Article_URLs)):
    #crawled_text.append(crawl_individual_page(get_bs4_content(Article_URLs[i])))
    f.write(crawl_individual_page(get_bs4_content(Article_URLs[i])) + "\n")
    print("SoupMaker & Scrapper running!\nProgress:" + str(i+1) +"/" + str(len(Article_URLs)))

'''
for i in range(len(Article_URLs)):
    print(crawled_text[i])
    print("\n")
'''

# close the output file
f.close()


## https://judgment.judicial.gov.tw/FJUD/data.aspx?ty=JD&id=TPDM%2c113%2c%e8%81%b2%2c1706%2c20240730%2c1&ot=in
## https://judgment.judicial.gov.tw/FJUD/data.aspx?ty=JD&id=TPDM%2c113%2c%e8%81%b2%2c1706%2c20240730%2c1&ot=in