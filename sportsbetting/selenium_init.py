"""
Initialisation de selenium
"""

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
    try:
        DRIVER = selenium.webdriver.Chrome("sportsbetting/resources/chromedriver", options=options)
    except selenium.common.exceptions.WebDriverException:
        DRIVER = selenium.webdriver.Chrome("sportsbetting/resources/chromedriver.exe", options=options)

