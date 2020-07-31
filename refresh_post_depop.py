from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import json
import time
import pickle

def nav_to_profile(driver, username, loadbearing_quirk=0):
    driver.find_element_by_css_selector('li[data-testid="navigation__profile"] > a[href="/{}/"]'.format(username)).click()

    #navigating from item page > profile requires two clicks - jquery quirk assumed
    if loadbearing_quirk:
        driver.find_element_by_css_selector('li[data-testid="navigation__profile"] > a[href="/{}/"]'.format(username)).click()

    if driver.current_url == 'https://www.depop.com/{}'.format(username):
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div[data-testid="product__items"]')))
    else:
        try:
            WebDriverWait(driver, 10).until(EC.url_changes('https://www.depop.com/{}'.format(username)))
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div[data-testid="product__items"]')))
        except TimeoutError:
            print('Error: Navigation to profile failed. Current URL is {}. URL should be {}.'.format(driver.current_url, 'https://www.depop.com/{}'.format(username)))
            raise BaseException

#with open('gitRepos/refreshPostDepop/credentials.json', 'r') as file:
with open('credentials.json', 'r') as file:
    login = json.load(file)

try:
    driver = webdriver.Chrome()
    driver.get('https://www.depop.com/login/')
    homepage_url = driver.current_url

    #login
    driver.find_element_by_id('username').send_keys(login['username'])
    driver.find_element_by_id('password').send_keys(login['pw'])
    driver.find_element_by_css_selector('#__next > div.styles__LoginContainer-sc-1y6oxke-0.csDotb > div:nth-child(1) > form > button').click()

    WebDriverWait(driver, 10).until(EC.url_changes(homepage_url))

    #logged in homepage > navigate to profile
    nav_to_profile(driver, login['username'])
    #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/div[4]/div/div[1]')))

    #scroll down for all divs to appear
    num_posts = len(driver.find_elements_by_css_selector('a[data-testid="product__item"]'))

    #refresh posts
    #alt - get cookies, go to each URL separately
    for i in range(1, num_posts+1):
        if driver.current_url == 'https://www.depop.com/westerchat/':
            item_name = driver.find_element_by_css_selector('a[data-testid="product__item"]:nth-child({}) > div > div > img'.format(i)).get_attribute('alt')
            driver.find_element_by_css_selector('a[data-testid="product__item"]:nth-child({})'.format(i)).click()
        else:
            print('Error: Should be on profile page, instead on {}'.format(driver.current_url))
            raise BaseException

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-testid="button__edit"')))
        driver.find_element_by_css_selector('a[data-testid="button__edit"').click()
        time.sleep(2)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"]')))
        save_btn = driver.find_element_by_css_selector('button[type="submit"]')

        #dismiss banner the first time around
        if i == 1:
            try:
                driver.find_element_by_xpath('/html/body/div/div[1]')
                driver.find_element_by_xpath('/html/body/div/div[1]/div/button').click()

            except NoSuchElementException:
                print('COVID Banner not found.')

        #2s sleep timer between each page or else changes may not persist despite running without error through site's flow
        save_btn.location_once_scrolled_into_view
        save_btn.click()
        time.sleep(2)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-testid="navigation__profile"] > a[href="/{}/"]'.format(login['username']))))
        nav_to_profile(driver, login['username'], loadbearing_quirk=1)
        time.sleep(2)

        print('Item {} added: {}'.format(i, item_name))

        #ActionChains(driver).move_to_element(save_btn).click().perform()

    #logout
    driver.find_element_by_css_selector('#mainNavigation > li:nth-child(5) > button').click()

finally:
    driver.close()
