from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import json
import time
import pickle

# function: repeatedly tries to click on a link for a specified number of times before failing
# parameters:
#   driver - selenium webdriver; selenium webdriver for session
#   webel - selenium webelement; selenium webelement to be clicked
#   ec_url_type - string "exact" or "changed"; two options indicates which EC method to use (check for exact URL or wait for current URL to change)
#   exact_url - string; if ec_url_type is "exact", provide the exact URL
#   current_url - string; if ec_url_type is "changed", provide current URL
#   repeat_click - int; max number of times to try re-clicking a webelement
#   two_second_wait - boolean; waits two seconds after initial webelement click before proceeding
# >15 posts may become too many APM for site
# mitigate with last 5 or add in 2s buffer
def repeat_click_if_timeout(driver, webel, ec_url_type, exact_url=None, current_url=None, repeat_click = 1, two_second_wait = False):
    attempt = 0
    url_diff = False

    while not url_diff:
        if attempt == repeat_click:
            raise TimeoutException('{} attempts reached'.format(repeat_click))

        print('web element clicked (repeat).')
        webel.click()

        if two_second_wait: #for too many APM
            time.sleep(2)

        try:
            if ec_url_type == 'exact':
                WebDriverWait(driver, 10).until(EC.url_to_be(exact_url))
            elif ec_url_type == 'changed':
                WebDriverWait(driver, 10).until(EC.url_changes(current_url))

            url_diff = True

        except TimeoutException:
            attempt += 1
            print("Navigation failed. Try again. Attempt: {}".format(attempt))
            print(current_url)

#function: scrolls the full length of the profile
#parameters:
#   driver - selenium driver; selenium driver for the session
#   num_posts - int; the total number of posts on the profile
def scroll_full_profile(driver, num_posts):
    current_num_post = 0

    while num_posts != current_num_post:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(2)
        current_num_post = len(driver.find_elements_by_css_selector('a[data-testid="product__item"]'))  # update

    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')

#function: scrolls the full length of the profile and returns the total number of posts on the profile
#parameter:
#   driver - selenium driver; selenium driver for the session
#   num_posts - int; the number of posts on the profile when you initially navigate to it
def full_profile_num_posts(driver, num_posts):
    current_num_post = 0

    # error out if there are no posts to update
    if num_posts == 0:
        print('Error: Profile contains no posts. ', num_posts)
        raise Exception

    while num_posts != current_num_post:
        current_num_post = num_posts
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(2)
        num_posts = len(driver.find_elements_by_css_selector('a[data-testid="product__item"]'))  # update

        print('previous number of posts: {}'.format(current_num_post))
        print('new number of posts: {}'.format(num_posts))

    return num_posts

# function: refreshes last 15 depop posts with 2s in between each refresh
# requires credentials file to hold login info as json in 'username' and 'pw' attributes
def main():
    num_posts_to_refresh = 15

    with open('credentials.json', 'r') as file:
        login = json.load(file)

    username = login['username']
    password = login ['pw']

    try:
        driver = webdriver.Chrome()
        driver.get('https://www.depop.com/login/')
        login_url = driver.current_url

        #login
        driver.find_element_by_id('username').send_keys(username)
        driver.find_element_by_id('password').send_keys(password)
        driver.find_element_by_css_selector('#__next > div.styles__LoginContainer-sc-1y6oxke-0.csDotb > div:nth-child(1) > form > button').click()

        WebDriverWait(driver, 10).until(EC.url_changes(login_url))
        homepage_url = driver.current_url

        #logged in homepage > navigate to profile
        driver.get('https://www.depop.com/{}'.format(username))
        WebDriverWait(driver, 10).until(EC.url_changes(homepage_url))

        #scroll down for all divs to appear
        time.sleep(2)
        num_posts = len(driver.find_elements_by_css_selector('a[data-testid="product__item"]')) #initialize

        num_posts=full_profile_num_posts(driver, num_posts)
        print('{} posts on profile.'.format(num_posts))

        #re-post the lesser of designated number of posts or total number of posts on profile
        if num_posts < num_posts_to_refresh:
            num_to_refresh = num_posts
        else:
            num_to_refresh = num_posts_to_refresh

        #refresh posts
        for i in range(1, num_to_refresh+1):

            #select the last post
            if driver.current_url == 'https://www.depop.com/{}/'.format(username):
                items = driver.find_elements_by_css_selector('a[data-testid="product__item"]:nth-child(1) > div > img')
                item_name = items[num_posts-1].get_attribute('alt')
                time.sleep(2)
                driver.find_elements_by_css_selector('a[data-testid="product__item"]:nth-child(1)')[num_posts-1].click()

            else:
                print('Error: Should be on profile page, instead on {}'.format(driver.current_url))
                raise BaseException

            #navigate to post
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

            print('trying to save')

            try:
                repeat_click_if_timeout(driver, save_btn, 'changed', current_url=edit_post_url, repeat_click=5)
                print('post saved')
            except TimeoutException:
                print('{} post failed to save. Check post for validity.'.format(edit_post_url))

            #for all but the last post, navigate back to profile
            if i != num_to_refresh:
                post_url = driver.current_url
                print(post_url)
                driver.get('https://www.depop.com/{}'.format(username))

                WebDriverWait(driver, 10).until(EC.url_changes(post_url))
                print(driver.current_url)
                time.sleep(2)

                scroll_full_profile(driver, num_posts)

            print('Item {} added: {}'.format(i, item_name))

            #ActionChains(driver).move_to_element(save_btn).click().perform()

        #logout
        driver.find_element_by_css_selector('#mainNavigation > li:nth-child(4) > div > div > svg').click()
        driver.find_element_by_css_selector('#userNavItem > button').click()
        time.sleep(5)
        # driver.find_element_by_css_selector('button[data-testid="navigation__logout"]').click()

    finally:
        driver.close()


if __name__ == '__main__':
    main()
