"""
Initialisation de selenium
"""

import colorama
import os
import selenium
import selenium.webdriver
import selenium.common
import sportsbetting
import termcolor
import time

PATH_DRIVER = os.path.dirname(sportsbetting.__file__) + "/resources/chromedriver"
DRIVER = {}


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
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-extensions")
    try:
        print(PATH_DRIVER)
        print("Version ancienne Windows")
        DRIVER[site] = selenium.webdriver.Chrome(PATH_DRIVER + "_older.exe", options=options)
    except selenium.common.exceptions.WebDriverException:
        try:
            print("Version Unix")
            DRIVER[site] = selenium.webdriver.Chrome(PATH_DRIVER, options=options)
        except OSError:
            print("Version Windows")
            DRIVER[site] = selenium.webdriver.Chrome(PATH_DRIVER + ".exe", options=options)
        except selenium.common.exceptions.WebDriverException:
            print("Wrong permissions, please make chromedriver executable")
            exit()
    colorama.init()
    print(termcolor.colored('Driver started for {}'.format(site), 'green'))
    colorama.Style.RESET_ALL
    colorama.deinit()

def scroll(driver, timeout):
    scroll_pause_time = timeout
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(scroll_pause_time)
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If heights are the same it will exit the function
            break
        last_height = new_height