"""
Initialisation de selenium
"""

import os
import selenium
import selenium.webdriver
import selenium.common
import sportsbetting

PATH_DRIVER = os.path.dirname(sportsbetting.__file__) + "/resources/chromedriver"
DRIVER = {}


def start_selenium(site):
    """
    Lancement d'un driver selenium
    """
    global DRIVER
    global PATH_DRIVER
    options = selenium.webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images': 2, 'disk-cache-size': 4096}
    options.add_argument('log-level=3')
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--headless")
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
