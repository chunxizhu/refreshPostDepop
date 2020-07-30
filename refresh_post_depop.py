from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import json
import pickle

with open('gitRepos/refreshPostDepop/credentials.json', 'r') as file:
    login = json.load(file)

try:
    driver = webdriver.Chrome()
    driver.get('https://www.depop.com/login/')
    current_url = driver.current_url

    #login
    driver.find_element_by_id('username').send_keys(login['username'])
    driver.find_element_by_id('password').send_keys(login['pw'])
    driver.find_element_by_css_selector('#__next > div.styles__LoginContainer-sc-1y6oxke-0.csDotb > div:nth-child(1) > form > button').click()

    WebDriverWait(driver, 10).until(EC.url_changes(current_url))
    current_url = driver.current_url

    #logged in homepage > navigate to profile
    driver.find_element_by_css_selector('#__next > header > div > div > button')
    WebDriverWait(driver, 10)

    element_found = False
    try:
        driver.find_element_by_css_selector('#mainNavigation > li:nth-child(3) > a').click()
        element_found = True
    except NoSuchElementException:
        pass

    try:
        if element_found == False:
            driver.find_element_by_css_selector('#__next > header > div > div > div > div > div > div > nav:nth-child(2) > ul > li:nth-child(2) > a').click()
    except NoSuchElementException:
        print('Profile button could not be found.')

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div[2]')))

    #gather all post elements
    all_posts_WebElements = driver.find_elements_by_xpath('/html/body/div/div[2]')

#__next > div.Container-sc-4caz4y-0.SearchResultsContainer-sc-10zc1ok-0.hjUyxE > div > div > a:nth-child(2)
#__next > div.Container-sc-4caz4y-0.SearchResultsContainer-sc-10zc1ok-0.hjUyxE > div > div.styles__ProductListContainer-sc-5cfswk-1.bMPICj > a:nth-child(1)
    print(len(all_posts_WebElements))

    #refresh posts
    #alt - get cookies, go to each URL separately
    for post in all_posts_WebElements:
        print(post)
        post.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_location((By.XPATH, '//*[@id="__next"]/div/div[1]/div[3]/div/div[3]/div/a[1]')))
        driver.find_element_by_css_selector('//*[@id="__next"]/div/div[1]/div[3]/div/div[3]/div/a[1]')

        WebDriverWait(driver, 10).until(EC.presence_of_element_location((By.XPATH, '/html/body/div/div/form/div[2]/button[1]')))
        driver.find_element_by_css_selector('/html/body/div/div/form/div[2]/button[1]').click()

    #logout
    driver.find_element_by_css_selector('#mainNavigation > li:nth-child(5) > button').click()

finally:
    driver.close()
