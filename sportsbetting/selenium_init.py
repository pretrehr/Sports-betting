"""
Initialisation de selenium
"""

import os
import selenium


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
    os.system("cd sportsbetting/resources")
    DRIVER = selenium.webdriver.Chrome("chromedriver", options=options)
    os.system("cd ../..")
