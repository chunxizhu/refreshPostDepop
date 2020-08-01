from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import json
import time
import pickle

# >15 posts may become too many APM for site
# mitigate with last 5 or add in 2s buffer
def repeat_click_if_timeout(driver, webel, ec_url_type, exact_url=None, current_url=None, repeat_click = 0, two_second_wait = False):
    attempt = 0
    on_profile = False

    while not on_profile:
        if attempt == 5:
            raise TimeoutException

        for i in range(repeat_click+1):
            webel.click()

        if two_second_wait: #for too many APM
            time.sleep(2)

        try:
            if ec_url_type == 'exact':
                WebDriverWait(driver, 10).until(EC.url_to_be(exact_url))
            elif ec_url_type == 'changed':
                WebDriverWait(driver, 10).until(EC.url_changes(current_url))

            on_profile = True

        except TimeoutException:
            attempt += 1
            print("Profile navigation failed. Try again. Attempt: {}".format(attempt))
            print(current_url)
            pass

def update_w_auto_wait():
    with open('credentials.json', 'r') as file:
        login = json.load(file)

    username = login['username']

    try:
        driver = webdriver.Chrome()
        driver.get('https://www.depop.com/login/')
        login_url = driver.current_url

        #login
        driver.find_element_by_id('username').send_keys(username)
        driver.find_element_by_id('password').send_keys(login['pw'])
        driver.find_element_by_css_selector('#__next > div.styles__LoginContainer-sc-1y6oxke-0.csDotb > div:nth-child(1) > form > button').click()

        WebDriverWait(driver, 10).until(EC.url_changes(login_url))
        homepage_url = driver.current_url

        #logged in homepage > navigate to profile
        profile_nav = driver.find_element_by_css_selector('li[data-testid="navigation__profile"] > a[href="/{}/"]'.format(username))
        repeat_click_if_timeout(driver, profile_nav, 'exact', 'https://www.depop.com/{}/'.format(username))
        WebDriverWait(driver, 10).until(EC.url_changes(homepage_url))

        #scroll down for all divs to appear
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-testid="product__item"]')))
        num_posts = len(driver.find_elements_by_css_selector('a[data-testid="product__item"]')) #initialize
        current_num_post = 0

        #error out if there are no posts to update
        if num_posts == 0:
            print('Error: Profile contains no posts. ', num_posts)
            raise Exception

        while num_posts != current_num_post:
            current_num_post = num_posts
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(2)
            num_posts = len(driver.find_elements_by_css_selector('a[data-testid="product__item"]')) #update

        print('{} posts on profile.'.format(num_posts))

        #refresh posts
        #alt - get cookies, go to each URL separately
        for i in range(1, num_posts+1):
            if driver.current_url == 'https://www.depop.com/{}/'.format(username):
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-testid="product__item"]:nth-child({}) > div > div > img'.format(i))))
                item_name = driver.find_element_by_css_selector('a[data-testid="product__item"]:nth-child({}) > div > div > img'.format(i)).get_attribute('alt')

                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-testid="product__item"]:nth-child({})'.format(i))))
                driver.find_element_by_css_selector('a[data-testid="product__item"]:nth-child({})'.format(i)).click()

            else:
                print('Error: Should be on profile page, instead on {}'.format(driver.current_url))
                raise BaseException

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-testid="button__edit"')))
            driver.find_element_by_css_selector('a[data-testid="button__edit"').click()

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"]')))
            save_btn = driver.find_element_by_css_selector('button[type="submit"]')
            edit_post_url = driver.current_url
            print(edit_post_url)

            #dismiss banner the first time around
            if i == 1:
                try:
                    driver.find_element_by_xpath('/html/body/div/div[1]')
                    driver.find_element_by_xpath('/html/body/div/div[1]/div/button').click()

                except NoSuchElementException:
                    print('COVID Banner not found.')

            #save post
            save_btn.location_once_scrolled_into_view
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))

            repeat_click_if_timeout(driver, save_btn, 'changed', current_url=edit_post_url)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'li[data-testid="navigation__profile"] > a[href="/{}/"]'.format(login['username']))))

            post_url = driver.current_url
            print(post_url)
            profile_nav = driver.find_element_by_css_selector(
                'li[data-testid="navigation__profile"] > a[href="/{}/"]'.format(username))
            repeat_click_if_timeout(driver, profile_nav, 'exact', 'https://www.depop.com/{}/'.format(username), repeat_click=1)   #navigating from item page > profile requires two clicks - jquery quirk assumed

            WebDriverWait(driver, 10).until(EC.url_changes(post_url))
            print(driver.current_url)
            time.sleep(2)

            print('Item {} added: {}'.format(i, item_name))

            #ActionChains(driver).move_to_element(save_btn).click().perform()

        #logout
        driver.find_element_by_css_selector('button[data-testid="navigation__logout"]').click()

    finally:
        driver.close()

