"""
Initialisation de selenium
"""

import selenium
import sportsbetting
import os

path_driver = os.path.dirname(sportsbetting.__file__)+"\\resources\\chromedriver"

def start_selenium():
    """
    Lancement d'un driver selenium
    """
    global DRIVER
    options = selenium.webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images':2, 'disk-cache-size': 4096}
    options.add_argument('log-level=3')
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--headless")
    try:
        print(path_driver)
        DRIVER = selenium.webdriver.Chrome(path_driver, options=options)
    except (selenium.common.exceptions.WebDriverException, OSError):
        DRIVER = selenium.webdriver.Chrome(path_driver+".exe", options=options)

