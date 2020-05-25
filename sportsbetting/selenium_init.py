"""
Initialisation de selenium
"""

import os
import selenium
import selenium.webdriver
import selenium.common
import sportsbetting

PATH_DRIVER = os.path.dirname(sportsbetting.__file__) + "\\resources\\chromedriver"
DRIVER = None


def start_selenium():
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
        DRIVER = selenium.webdriver.Chrome(PATH_DRIVER + ".exe", options=options)
    except (selenium.common.exceptions.WebDriverException, OSError):
        DRIVER = selenium.webdriver.Chrome(PATH_DRIVER, options=options)
    except selenium.common.exceptions.SessionNotCreatedException:
        DRIVER = selenium.webdriver.Chrome(PATH_DRIVER + "_older.exe", options=options)
