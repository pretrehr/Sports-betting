"""
Initialisation de selenium
"""

import colorama
import selenium
import selenium.webdriver
import selenium.common
import stopit
import termcolor

import sportsbetting

DRIVER = {}


@stopit.threading_timeoutable(timeout_param='timeout')
def start_selenium(site, headless=True):
    """
    Lancement d'un driver selenium
    """
    options = selenium.webdriver.ChromeOptions()
    prefs = {'profile.managed_default_content_settings.images': 2,
             'disk-cache-size': 4096}
    options.add_argument('log-level=3')
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-extensions")
    try:
        DRIVER[site] = selenium.webdriver.Chrome(
            sportsbetting.PATH_DRIVER, options=options)
        colorama.init()
        print(termcolor.colored('Driver started for {}{}'
                                .format(site, colorama.Style.RESET_ALL),
                                'green'))
        colorama.deinit()
        return True
    except (stopit.utils.TimeoutException,
            selenium.common.exceptions.SessionNotCreatedException):
        colorama.init()
        print(termcolor.colored('Driver not started for {}{}'
                                .format(site, colorama.Style.RESET_ALL),
                                'red'))
        colorama.deinit()
        return False
