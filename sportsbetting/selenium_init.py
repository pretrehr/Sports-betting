"""
Initialisation de selenium
"""

import colorama
import os
import selenium
import selenium.webdriver
import selenium.common
import sportsbetting
import stopit
import termcolor
import time

PATH_DRIVER = os.path.dirname(sportsbetting.__file__) + "/resources/chromedriver"
DRIVER = {}


@stopit.threading_timeoutable(timeout_param='timeout')
def start_selenium(site, headless=True):
    """
    Lancement d'un driver selenium
    """
    global DRIVER
    global PATH_DRIVER
    options = selenium.webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images': 2, 'disk-cache-size': 4096}
    options.add_argument('log-level=3')
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-extensions")
    try:
        DRIVER[site] = selenium.webdriver.Chrome(options=options)
        colorama.init()
        print(termcolor.colored('Driver started for {}'.format(site), 'green'))
        colorama.Style.RESET_ALL
        colorama.deinit()
        return True
    except stopit.utils.TimeoutException:
        colorama.init()
        print(termcolor.colored('Driver not started for {}'.format(site), 'red'))
        colorama.Style.RESET_ALL
        colorama.deinit()
        return False

def scroll(driver, timeout):
    scroll_pause_time = timeout
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight-1200);")
        # Wait to load page
        time.sleep(scroll_pause_time)
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If heights are the same it will exit the function
            break
        last_height = new_height