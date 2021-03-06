"""Helper functions for OpenStax Pages."""

from collections import OrderedDict
from http.client import responses
from platform import system
from random import randint, sample
from time import sleep
from typing import Tuple, Union
from warnings import warn

import requests
from faker import Faker
from pypom import Page, Region
from selenium.common.exceptions import (  # NOQA
    ElementClickInterceptedException,  # NOQA
    NoSuchElementException,  # NOQA
    StaleElementReferenceException,  # NOQA
    TimeoutException,  # NOQA
    WebDriverException)  # NOQA
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as expect
from selenium.webdriver.support.color import Color
from selenium.webdriver.support.ui import Select, WebDriverWait
from simple_salesforce import Salesforce as SF

JAVASCRIPT_CLICK = 'arguments[0].click()'
OPEN_TAB = 'window.open();'
SCROLL_INTO_VIEW = 'arguments[0].scrollIntoView();'
SHIFT_VIEW_BY = 'window.scrollBy(0, arguments[0])'

JQUERY = 'https://code.jquery.com/jquery-3.3.1.slim.min.js'
WAIT_FOR_IMAGE = ('https://cdnjs.cloudflare.com/ajax/libs/'
                  'jquery.waitforimages/1.5.0/jquery.waitforimages.min.js')

STATE_PROV = [
    ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'),
    ('AR', 'Arkansas'), ('CA', 'California'), ('CO', 'Colorado'),
    ('CT', 'Connecticut'), ('DE', 'Delaware'), ('FL', 'Florida'),
    ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
    ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'),
    ('KS', 'Kansas'), ('KY', 'Kentucky'), ('LA', 'Louisiana'),
    ('ME', 'Maine'), ('MD', 'Maryland'), ('MA', 'Massachusetts'),
    ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MO', 'Missouri'),
    ('MS', 'Mississippi'), ('MT', 'Montana'), ('NE', 'Nebraska'),
    ('NV', 'Nevada'), ('NH', 'New Hampshire'), ('NJ', 'New Jersey'),
    ('NM', 'New Mexico'), ('NY', 'New York'), ('NC', 'North Carolina'),
    ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
    ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'),
    ('SC', 'South Carolina'), ('SD', 'South Dakota'), ('TN', 'Tennessee'),
    ('TX', 'Texas'), ('UT', 'Utah'), ('VT', 'Vermont'), ('VA', 'Virginia'),
    ('WA', 'Washington'), ('WV', 'West Virginia'), ('WI', 'Wisconsin'),
    ('WY', 'Wyoming'), ('AS', 'American Samoa'),
    ('DC', 'District of Columbia'), ('FM', 'Federated States of Micronesia'),
    ('GU', 'Guam'), ('MP', 'Northern Mariana Islands'), ('PW', 'Palau'),
    ('PR', 'Puerto Rico'), ('VI', 'Virgin Islands'),
    ('AA', 'Armed Forces Americas'), ('AE', 'Armed Forces Europe'),
    ('AP', 'Armed Forces Pacific'), ('AB', 'Alberta'),
    ('BC', 'British Columbia'), ('MB', 'Manitoba'), ('NB', 'New Brunswick'),
    ('NF', 'Newfoundland'), ('NT', 'Northwest Territories'),
    ('NS', 'Nova Scotia'), ('ON', 'Ontario'), ('PE', 'Prince Edward Island'),
    ('PQ', 'Province du Quebec'), ('SK', 'Saskatchewan'),
    ('YT', 'Yukon Territory')]

Name = Tuple[str, str, str, str]


class Utility:
    """Helper functions for various Pages actions."""

    HEX_DIGITS = '0123456789ABCDEF'

    @classmethod
    def clear_field(cls, driver, field=None, field_locator=None):
        """Clear the contents of text-type fields.

        :param driver: a selenium webdriver
        :param field: an input field to interact with
        :param field_locator: a By selector tuple (str, str)
        :returns: None
        """
        sleep(0.1)
        if not field:
            field = driver.find_element(*field_locator)
        if driver.name == 'chrome':
            field.clear()
        elif driver.name == 'firefox':
            special = Keys.COMMAND if system() == 'Darwin' else Keys.CONTROL
            ActionChains(driver) \
                .click(field) \
                .key_down(special) \
                .send_keys('a') \
                .key_up(special) \
                .send_keys(Keys.DELETE) \
                .perform()
        else:
            clear = []
            for _ in range(len(field.get_attribute('value'))):
                clear.append(Keys.DELETE)
                clear.append(Keys.BACKSPACE)
            field.send_keys(clear)

    @classmethod
    def click_option(cls, driver,
                     locator=None, element=None, force_js_click=False):
        """Standardize element clicks to avoid cross-browser issues."""
        element = element if element else driver.find_element(*locator)
        cls.scroll_to(driver=driver, element=element, shift=-80)
        sleep(0.5)
        try:
            if force_js_click or \
                    driver.capabilities.get('browserName').lower() == 'safari':
                raise WebDriverException('Bypassing the driver-defined click')
            element.click()
        except WebDriverException:
            for _ in range(10):
                try:
                    driver.execute_script(JAVASCRIPT_CLICK, element)
                    break
                except ElementClickInterceptedException:  # Firefox issues
                    sleep(1.0)
                except NoSuchElementException:  # Safari issues
                    if locator:
                        element = driver.find_element(*locator)
                except StaleElementReferenceException:  # Chrome and Firefox
                    if locator:
                        element = driver.find_element(*locator)

    @classmethod
    def close_tab(cls, driver):
        """Close the current tab and switch to the other tab.

        :param driver: a selenium webdriver
        :returns: None
        """
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        sleep(1.0)

    @classmethod
    def compare_colors(cls, left, right):
        """Return True if two RGB color strings match.

        :param left: a color string
        :param right: a color string
        :returns: True if the color strings match
        """
        return Color.from_string(left) == Color.from_string(right)

    @classmethod
    def fake_email(cls, first_name, surname, _id=False):
        """Return a name-based fake email.

        :param first_name: a user's first name
        :param surname: a user's last or surname
        :param _id: an ID string to append to the name
        :returns: a compound RestMail email address string
        """
        id_string = _id if _id else cls.random_hex(cls.random(4, 7))
        return f'{first_name}.{surname}.{id_string}@restmail.net'.lower()

    @classmethod
    def fast_multiselect(cls, driver, element_locator, labels):
        """Select menu multiselect options.

        :param driver: a selenium webdriver
        :param element_locator: an element selector tuple (str, str)
        :param labels: a list of menu options to select
        :returns: the Select object

        Daniel Abel multiselect
        'https://sqa.stackexchange.com/questions/1355/
        what-is-the-correct-way-to-select-an-option-using-seleniums-
        python-webdriver#answer-2258'
        """
        menu = driver.find_element(*element_locator)
        cls.scroll_to(driver, element=menu)
        select = Select(menu)
        for label in labels:
            select.select_by_visible_text(label)
        return select

    @classmethod
    def get_error_information(cls, error):
        """Break up an assertion error object.

        :param error: the assertion error object
        :returns: a modified error message as a string
        """
        short = str(error.getrepr(style='short'))
        info = short.split('AssertionError: ')[-1:][0]
        return info.replace("'", '').replace('{', '').replace('}', '')

    @classmethod
    def get_test_credit_card(cls, card=None, status=None):
        """Return a random card number and CVV for test transactions.

        :param card: a credit card type like VISA or MasterCard
        :param status: a credit card status
        :returns: a tuple of the credit card number and the CVV number
        """
        braintree = Card()
        _card = card if card else Status.VISA
        _status = status if status else Status.VALID
        test_cards = braintree.get_by(Status.STATUS, _status)
        test_cards = braintree.get_by(Status.TYPE, _card, test_cards)
        select = randint(0, len(test_cards) - 1)
        use_card = test_cards[select]
        return (use_card['number'], use_card['cvv'])

    @classmethod
    def has_children(cls, element: WebElement) -> bool:
        """Return True if a specific element has one or more children.

        :param WebElement element: a webelement
        :return: ``True`` if the element has one or more child elements
        :rtype: bool

        """
        if not element:
            return False
        return len(element.find_elements('xpath', './*')) > 0

    @classmethod
    def has_height(cls, driver, locator):
        """Return True if the computed height isn't 'auto'.

        :param driver: a selenium webdriver
        :param locator: a CSS selector for an element
        :returns: True if the element's height is not 'auto'
        """
        auto = ('return window.getComputedStyle('
                f'document.querySelector("{locator}")).height != "auto";')
        return driver.execute_script(auto)

    @classmethod
    def in_viewport(cls, driver, locator=None, element=None,
                    ignore_bottom=False, display_marks=True):
        """Return True if the element boundry completely lies in view.

        :param driver: a selenium webdriver
        :param locator: an element selector tuple
        :param element: a webelement
        :param ignore_bottom: skip the check that the element is above the
            bottom of the browser window
        :param display_marks: output the bounding box values and checks to
            stdout
        :returns: True if the element box is within the browser window
        """
        LEFT, TOP, RIGHT, BOTTOM = range(4)
        target = element if element else driver.find_element(*locator)
        rect = driver.execute_script(
            'return arguments[0].getBoundingClientRect();', target)
        if display_marks:
            print('Rectangle: {0}'.format(rect))
        page_x_offset = driver.execute_script('return window.pageXOffset;')
        page_y_offset = driver.execute_script('return window.pageYOffset;')
        target_boundry = (
            rect.get('left') + page_x_offset,
            rect.get('top') + page_y_offset,
            rect.get('right') + page_x_offset,
            rect.get('bottom') + page_y_offset)
        window_width = driver.execute_script(
            'return document.documentElement.clientWidth;')
        window_height = driver.execute_script(
            'return document.documentElement.clientHeight;')
        page_boundry = (
            page_x_offset,
            page_y_offset,
            page_x_offset + window_width,
            page_y_offset + window_height)
        if display_marks:
            base = '{side} {result} - Element ({element}) {sign} Page ({page})'
            bottom = (
                'Bottom {result} - [Element ({element}) {sign} '
                'Page ({page})] or [Skip Bottom ({skip})]')
            print(base.format(
                side='Left', sign='>=', page=page_boundry[LEFT],
                result=target_boundry[LEFT] >= page_boundry[LEFT],
                element=target_boundry[LEFT]))
            print(base.format(
                side='Top', sign='>=', page=page_boundry[TOP],
                result=target_boundry[TOP] >= page_boundry[TOP],
                element=target_boundry[TOP]))
            print(base.format(
                side='Right', sign='<=', page=page_boundry[RIGHT],
                result=target_boundry[RIGHT] <= page_boundry[RIGHT],
                element=target_boundry[RIGHT]))
            print(bottom.format(
                sign='<=', page=page_boundry[BOTTOM],
                result=(
                    target_boundry[BOTTOM] <= page_boundry[BOTTOM] or
                    ignore_bottom),
                element=target_boundry[BOTTOM], skip=ignore_bottom))
        return (
            target_boundry[LEFT] >= page_boundry[LEFT] and
            target_boundry[TOP] >= page_boundry[TOP] and
            target_boundry[RIGHT] <= page_boundry[RIGHT] and
            (target_boundry[BOTTOM] <= page_boundry[BOTTOM] or
             ignore_bottom))

    @classmethod
    def is_image_visible(cls, driver, image=None, locator=None):
        """Return True if an image is rendered."""
        if image:
            image_group = image if isinstance(image, list) else [image]
        else:
            image_group = driver.find_elements(*locator)
            auto = ('return window.getComputedStyle('
                    'arguments[0]).height!="auto"')
            image_group = list(filter(
                lambda img: driver.execute_script(auto, img),
                image_group))
        ie = 'internet explorer'
        from selenium.webdriver import Ie
        if (isinstance(driver, Ie) or
                driver.capabilities.get('browserName') == ie):
            script = 'return arguments[0].complete'
        else:
            script = (
                'return ((typeof arguments[0].naturalWidth)!="undefined")')
        from functools import reduce
        map_list = (list(map(
            lambda img: driver.execute_script(script, img), image_group)))
        return reduce(lambda img, group: img and group, map_list, True)

    @classmethod
    def is_browser(cls, driver, browser='safari') -> bool:
        """Return True if the driver matches an expected browser.

        :param driver: a selenium webdriver instance
        :type driver: :py:class:`~selenium.webdriver.*.webdriver.WebDriver`
        :param str browser: (optional) the browser name
            `chrome`, `firefox`, or `safari`
        :return: ``True`` if the browser in use is a specific browser,
            otherwise ``False``
        :rtype: bool

        """
        return \
            driver.capabilities.get('browserName').lower() == browser.lower()

    @classmethod
    def load_background_images(cls, driver, locator):
        """Inject a script to wait for background image downloads.

        :param driver: a selenium webdriver instance
        :param locator: a CSS selector for background image elements
        :returns: True when complete so it can be used in loaded methods.
        """
        inject = (
            r'''
            ;(function() {
                var head = document.getElementsByTagName("head")[0];
                var jquery = document.createElement("script");
                jquery.src = "JQUERY_STRING";
                jquery.onload = function() {
                    var $ = window.jQuery;
                    var head = document.getElementsByTagName("head")[0];
                    var image = document.createElement("script");
                    image.src = "IMAGE_STRING";
                    image.type = "text/javascript";
                    head.appendChild(image);
                    $("SELECTOR").waitForImages().done(
                        function() { return true; });
                };
                head.appendChild(jquery);
            });
            return true;
            '''
            .replace('JQUERY_STRING', JQUERY)
            .replace('IMAGE_STRING', WAIT_FOR_IMAGE)
            .replace('SELECTOR', locator[1])
        )
        return driver.execute_script(inject)

    @classmethod
    def new_tab(cls, driver):
        """Open another browser tab."""
        driver.execute_script(OPEN_TAB)
        sleep(1)
        return driver.window_handles

    @classmethod
    def parent_page(cls, region: Region) -> Page:
        """Return the first page object found.

        :param region: the current region object in a page object tree
        :type region: :py:class:`~pypom.Region`
        :return: the first ``Page`` object found in the current tree
        :rtype: :py:class:`~pypom.Page`

        """
        if isinstance(region.page, Region):
            return cls.parent_page(region.page)
        return region.page

    @classmethod
    def random(cls, start=0, end=100000):
        """Return a random integer from start to end."""
        if start >= end:
            return start
        return randint(start, end)

    @classmethod
    def random_address(cls, string=False):
        """Return a fake mailing address."""
        fake = Faker()
        address = ['', '', '', '']
        use_abrev = randint(0, 1)
        address[0] = fake.street_address()
        address[1] = fake.city()
        address[2] = STATE_PROV[randint(0, len(STATE_PROV) - 1)][use_abrev]
        address[3] = fake.postcode().split('-')[0]
        return address

    @classmethod
    def random_hex(cls, length=20, lower=False):
        """Return a random hex number of size length."""
        line = ''.join([cls.HEX_DIGITS[randint(0, 0xF)]
                       for _ in range(length)])
        return line if not lower else line.lower()

    @classmethod
    def random_name(cls, is_male: bool = None, is_female: bool = None) \
            -> Name:
        """Generate a random name.

        If neither parameter is sent, generate either a male or female name.

        :param bool is_male: (optional) generate a generalized male name
        :param bool is_female: (optional) generate a generalized female name
        :return: the random name that may contain a title and/or a suffix
        :rtype: tuple(str, str, str, str)

        """
        fake = Faker()
        male = True if is_male else False if is_female else cls.random(0, 1)

        title = '' if cls.random(0, 9) < 6 else \
                fake.prefix_male() if male else fake.prefix_female()
        first = fake.first_name_male() if male else fake.first_name_female()
        last = fake.last_name()
        suffix = '' if cls.random(0, 9) < 8 else \
                 fake.suffix_male() if male else fake.suffix_female()

        return (title, first, last, suffix)

    @classmethod
    def random_phone(cls,
                     area_code: Union[int, str] = 713,
                     number_only: bool = True) -> str:
        """Return a random phone number.

        :param area_code: (optional) a U.S. phone number area code
        :type area_code: int or str
        :param bool number_only: (optional) return a number-only phone string
        :return: a U.S. generic telephone number
        :rtype: str

        """
        if number_only:
            return f'{area_code}5550{cls.random(100, 199)}'
        return f'({area_code}) 555-0{cls.random(100, 199)}'

    @classmethod
    def random_set(cls, group, size=1):
        """Return a unique set from a list."""
        if size <= 0:
            return []
        if size >= len(group):
            return group
        new_set = []
        while len(new_set) < size:
            selected = group[cls.random(0, len(group) - 1)]
            if selected not in new_set:
                new_set.append(selected)
        return new_set

    @classmethod
    def sample(cls, original_list: list, sample_size: int) -> list:
        """Return a sample of the original list.

        If the sample size is greater than the list size or the sample size is
        negative, return the original list.

        :param list original_list: the base list
        :param int sample_size: the maximum number of items to return
        :return: the sample from the original list
        :rtype: list

        """
        max_size = len(original_list)
        if sample_size >= max_size or sample_size < 0:
            return original_list
        return sample(original_list, sample_size)

    @classmethod
    def scroll_bottom(cls, driver):
        """Scroll to the bottom of the browser screen."""
        driver.execute_script(
            'window.scrollTo(0, document.body.scrollHeight);')
        sleep(0.75)

    @classmethod
    def scroll_to(
            cls, driver, element_locator=None, element=None, shift=0):
        """Scroll the screen to the element.

        :param driver: the selenium webdriver browser object
        :param element_locator: a By selector and locator tuple (str, str)
        :param element: a specific webelement
        :param shift: adjust the page vertically by a set number of pixels
                > 0 scrolls down, < 0 scrolls up
        :returns: None
        """
        target = element if element else driver.find_element(*element_locator)
        driver.execute_script(SCROLL_INTO_VIEW, target)
        if shift != 0:
            driver.execute_script(SHIFT_VIEW_BY, shift)

    @classmethod
    def scroll_top(cls, driver):
        """Scroll to the top of the browser screen.

        :param driver: the selenium webdriver object
        :returns: None
        """
        driver.execute_script('window.scrollTo(0, 0);')
        sleep(0.75)

    @classmethod
    def select(cls, driver, element_locator, label):
        """Select an Option from a menu."""
        return cls.fast_multiselect(driver, element_locator, [label])

    @classmethod
    def selected_option(cls, driver, element_locator):
        """Return the currently selected option."""
        return Select(driver.find_element(*element_locator)) \
            .first_selected_option \
            .text

    @classmethod
    def summed_list(cls, length=4, total=100, use_float=False):
        """Generate random, positive numbers that add up to a total.

        :param length: the number of values in the resulting list
        :param total: the summation of the values
        :param use_float: return floating point values instead of integers
        :returns: a list of values that equal the requested total
        :raises ValueError: invalid parameters
            length must be greater than or equal to one
            total must be greater than or equal to zero
        """
        if length < 1:
            raise(ValueError("The list length must be >= 1"))
        if total < 0:
            raise(ValueError("The sum (total) must be >= 0"))
        from random import random as random_decimal
        setup = float if use_float else int
        group = ([setup(0)] +
                 sorted(setup(random_decimal() * total)
                        for _ in range(length - 1)) +
                 [setup(total)])
        return [group[i + 1] - group[i] for i in range(len(group) - 1)]

    @classmethod
    def switch_to(cls, driver, link_locator=None, element=None, action=None,
                  force_js_click=False):
        """Switch to the other window handle."""
        current = driver.current_window_handle
        data = None
        if not action:
            cls.click_option(driver=driver, locator=link_locator,
                             element=element, force_js_click=force_js_click)
        else:
            data = action()
        sleep(1)
        new_handle = 1 if current == driver.window_handles[0] else 0
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[new_handle])
        if data:
            return data

    @classmethod
    def test_url_and_warn(cls, _head=True, code=None, url=None, link=None,
                          message='', driver=None):
        """Query a URL and return a warning if the code is not a success."""
        if driver:
            browser = driver.capabilities.get('browserName', '').lower()
        agent = {
            'chrome': {
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6)'
                    ' AppleWebKit/537.36 (KHTML, like Gecko)'
                    ' Chrome/77.0.3865.90 Safari/537.36'), },
            'firefox': {
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14;'
                    ' rv:69.0) Gecko/20100101 Firefox/69.0'), },
            'safari': {
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6)'
                    ' AppleWebKit/605.1.15 (KHTML, like Gecko)'
                    ' Version/13.0.1 Safari/605.1.15'), },
            '': {},
        }
        if link:
            url = link.get_attribute('href')
        test = requests.head(url) if _head \
            else requests.get(url, headers=agent.get(browser))
        code = test.status_code
        if code == 403 and _head:
            _head = False
            test = requests.get(url, headers=agent.get(browser))
            code = test.status_code
        if code == 503 or \
                'Error from cloudfront' in test.headers.get('X-Cache', ''):
            for _ in range(20):
                sleep(3)
                test = requests.head(url) if _head \
                    else requests.get(url, headers=agent.get(browser))
                code = test.status_code
                if code != 503:
                    break
        if code >= 400:
            # the test ran into a problem with the URL query
            status = ('<{code} {reason}>'
                      .format(code=code, reason=responses.get(code)))
            warn(UserWarning(
                '"{article}" returned a {status}'
                .format(article=message, status=status)))
            if 'Error from cloudfront' in test.headers.get('X-Cache', ''):
                return True
            return False
        return True

    @classmethod
    def wait_for_overlay(cls, driver, locator):
        """Wait for an overlay to clear making the target available."""
        WebDriverWait(driver, 15).until(
            expect.element_to_be_clickable(locator))
        sleep(1.0)

    @classmethod
    def wait_for_overlay_then(cls, target, time=10.0, interval=0.5):
        """Wait for an overlay to clear then performing the target action."""
        for _ in range(int(time / interval)):
            try:
                target()
                break
            except WebDriverException:
                sleep(interval)
        sleep(1.0)


class Card:
    """Fake card objects."""

    def __init__(self):
        """Retrieve card numbers from BTP."""
        import requests
        from bs4 import BeautifulSoup

        braintree = (
            'https://developers.braintreepayments.com/'
            'reference/general/testing/python'
        )
        section_list_selector = 'table:nth-of-type({position}) tbody tr'
        response = requests.get(braintree)
        if response.status_code != requests.codes.ok:
            response.raise_for_status()
        resp = BeautifulSoup(response.text, 'html.parser')
        self.options = []

        for card_status in range(Status.VALID, Status.OTHER + 1):
            for card in resp.select(
                    section_list_selector.format(position=card_status)):
                fields = card.select('td')
                card_processor = (Status.VISA
                                  if fields[0].text[0] == '4'
                                  else fields[1].text)
                if card_processor == Status.AMEX:
                    cvv = '{:04}'.format(randint(0, 9999))
                else:
                    cvv = '{:03}'.format(randint(0, 999))
                rest = fields[2].text if len(fields) > 2 else ''
                data = fields[1].text if card_status == Status.OTHER or  \
                    card_status == Status.TYPED else ''
                self.options.append({
                    'number': fields[0].text,
                    'cvv': cvv,
                    'type': card_processor,
                    'status': card_status,
                    'response': rest,
                    'data': data,
                })

    def get_by(self, field=None, state=None, use_list=None):
        """Return a subset of test cards with a specific type."""
        _field = field if field else Status.STATUS
        _state = state if state else Status.VALID
        _use_list = use_list if use_list else self.options
        return list(
            filter(
                lambda card: card[_field] == _state,
                _use_list
            )
        )

    def generic(self):
        """Return a random, valid test card."""
        cards = self.get_by()
        return cards[randint(0, len(cards) - 1)]


class Status:
    """Card states."""

    STATUS = 'status'
    VALID = 2
    NO_VERIFY = 3
    TYPED = 4
    OTHER = 5

    TYPE = 'type'
    AMEX = 'American Express'
    DINERS = 'Diners Club'
    DISCOVER = 'Discover'
    JCB = 'JCB'
    MAESTRO = 'Maestro'
    MC = 'Mastercard'
    VISA = 'Visa'

    RESPONSE = 'response'
    DECLINED = 'processor declined'
    FAILED = 'failed (3000)'


def go_to_(destination):
    """Follow a destination link and wait for the page to load."""
    return go_to_external_(destination)


def go_to_external_(destination, url=None):
    """Follow an external destination link repeatedly waiting for page load."""
    if url:
        try:
            destination.wait_for_page_to_load()
            return destination
        except TimeoutException:
            destination.driver.get(url)
            sleep(1)
    try:
        destination.wait_for_page_to_load()
        return destination
    except TimeoutException:
        raise TimeoutException(
            'Expected page <{_class}> failed to load{url}; ended at: {finish}'
            .format(_class=type(destination).__name__,
                    url=f' (URL: {url})' if url else '',
                    finish=destination.driver.current_url))


class Actions(ActionChains):
    """Add a javascript retrieval action and a data return perform."""

    def get_js_data(self, css_selector=None, data_type=None, expected=None,
                    element=None, new_script=None):
        """Trigger a style lookup."""
        if element:
            self._actions.append(
                lambda: self.data_read(element=element,
                                       data_type=data_type,
                                       expected=expected))
        elif new_script:
            self._actions.append(
                lambda: self.data_read(new_script=new_script,
                                       element=element,
                                       expected=expected))
        else:
            self._actions.append(
                lambda: self.data_read(css_selector=css_selector,
                                       data_type=data_type,
                                       expected=expected))
        result = None
        if self._driver.w3c:
            try:
                self.w3c_actions.perform()
            except TypeError:
                pass
            if element:
                result = self.data_read(element=element,
                                        data_type=data_type,
                                        expected=expected)
            elif new_script:
                result = self.data_read(new_script=new_script,
                                        element=element,
                                        expected=expected)
            else:
                result = self.data_read(css_selector=css_selector,
                                        data_type=data_type,
                                        expected=expected)
        else:
            for action in self._actions:
                result = action()
        sleep(1)
        return result

    def data_read(self, css_selector=None, data_type=None, expected=None,
                  element=None, new_script=None):
        """Compare the script return to an expected value."""
        if new_script:
            script = new_script
        elif element:
            script = (
                'return window.getComputedStyle(arguments[0])["{data_type}"]'
            ).format(data_type=data_type)
        else:
            script = (
                'return window.getComputedStyle(document.querySelector'
                '("{selector}"))["{data_type}"]'
            ).format(selector=css_selector, data_type=data_type)
        val = self._driver.execute_script(script, element)
        print(val, expected, val == expected)
        return [val == expected, val, expected]

    def wait(self, seconds: float):
        """Sleep for a specified number of seconds within an ActionChain."""
        self._actions.append(lambda: sleep(seconds))
        return self


class Record:
    """A Salesforce API result record."""

    def __init__(self, record: OrderedDict, **kwargs):
        """Initialize a Salesforce record."""
        self.url = record['attributes']['url']
        self.id = record['Account_ID__c']
        super().__init__(**kwargs)


class Salesforce:
    """Read object for Salesforce verification."""

    CONTACT = (
        "SELECT "
        "AccountId,Account_Email_verified__c,Address_Verified_Date__c,"
        "All_Emails__c,Books_Adopted__c,BookURL__c,Confirmed_Emails__c,"
        "CreatedDate,Domain__c,Donations__c,Email,Faculty_Confirmed_Date__c,"
        "Faculty_Verified__c,FirstName,From_Lead__c,HasOptedOutOfEmail,"
        "Has_filled_out_Adoption_Form__c,Id,Interested_in_Rover__c,"
        "LastModifiedDate,LastName,LeadSource,Leads__c,LongID__c,"
        "MailingAddress,MailingCity,MailingCountry,MailingCountryCode,"
        "Manual_Check__c,Marketing_Group__c,Market_Group__c,Name,"
        "Newsletter_Opt_Out__c,Number_of_Subjects__c,Phone,PositionT__c,"
        "Position__c,Salutation,School_Type__c,Search_Box__c,"
        "SendFacultyVerificationTo__c,Subject__c,SystemModstamp,Theme__c "
        "FROM Contact "
        "WHERE Search_Box__c = 'Automation' "
        "ORDER BY LastName,FirstName ASC NULLS FIRST"
    )
    LEAD = (
        "SELECT "
        "Account_ID__c,Adoption_Status__c,Book__c,Company,Complete__c,"
        "Confirmed_Date__c,Contact_ID__c,Contact_Name__c,Contact__c,"
        "Converted_Date__c,Country,CountryCode,Course_Code__c,Course_Name__c,"
        "CreatedDate,Dept_student_number__c,Email,Faculty_Book__c,"
        "Faculty_Website__c,Feedback_Response_Status__c,Feedback__c,FirstName,"
        "HasOptedOutOfEmail,How_did_you_Hear__c,Id,Institutional_Email__c,"
        "Institution_Type__c,IsConverted,LastActivityDate,LastModifiedDate,"
        "LastName,LeadSource,Name,Needs_Deletion__c,Needs__c,"
        "Newsletter_Opt_In__c,Newsletter__c,Number_of_Students__c,"
        "OS_Accounts_ID__c,Partner_Category_Interest__c,"
        "Partner_Interest_Other__c,Partner_Interest__c,Partner_Present__c,"
        "Phone,pi__campaign__c,pi__created_date__c,Reject_Reason__c,Role__c,"
        "School__c,Section_Numbers__c,Status,Status__c,Student_No_Status__c,"
        "Subject__c,SystemModstamp,TermYear__c,Term__c,test__c,Website,"
        "What_Happened__c "
        "FROM Lead "
        "WHERE Company='Automation' "
        "ORDER BY LastName,FirstName ASC NULLS FIRST"
    )
    ORGANIZATION = (
        "SELECT "
        "BillingCity,BillingCountry,BillingCountryCode,BillingPostalCode,"
        "BillingState,BillingStateCode,BillingStreet,Continent__c,CreatedDate,"
        "Description,Domain__c,HTML_Name__c,Id,LastModifiedDate,Name,"
        "Number_of_Adoptions__c,Phone,SystemModstamp,Type,Website "
        "FROM Account"
    )

    def __init__(self, username: str, password: str,
                 domain: str = 'test', query: str = ''):
        """Initialize the Salesforce request.

        :param str username: the Salesforce username
        :param str password: the Salesforce user password
        :param str domain: (optional) ```'test'``` if accessing a Salesforce
            sandbox, otherwise ```''```
        :param str query: (optional) the SOQL request

        """
        self._sf = SF(username=username, password=password, domain=domain)
        if query:
            self.query(query)
        else:
            self._size = 0
            self._records = []
            self.records = []

    def query(self, query: str, record_type: Record = None):
        """Send an SOQL request to Salesforce.

        :param str query: the SOQL request
        :return: None

        """
        results = self._sf.query(query)
        self._size = results.get('totalSize', 0)
        self._records = results.get('records', [])
        self.records = []
        additional_records = results.get('nextRecordUrl', '').split('/')[-1]
        while additional_records:
            results = self._sf.query_more(additional_records)
            self._records = self._records + results.get('records', [])
            additional_records = (
                results.get('nextRecordUrl', '').split('/')[-1])
        if record_type:
            for record in self._records:
                self.records.append(record_type(record))

    class Contact(Record):
        """A Salesforce contact."""

        def __init__(self, record: OrderedDict, **kwargs):
            """Initialize a Salesforce contact record."""
            super(Record, self).__init__(record=record, **kwargs)
            self.email_verified = record['Account_Email_verified__c']
            self.all_emails = record['All_Emails__c']
            self.books_adopted = record['Books_Adopted__c']
            self.confirmed_emails = record['Confirmed_Emails__c']
            self.created_on = record['CreatedDate']
            self.domain = record['Domain__c']
            self.donations = record['Donations__c']
            self.email = record['Email']
            self.faculty_verified = record['Faculty_Verified__c']
            self.first_name = record['FirstName']
            self.from_lead = record['From_Lead__c']
            self.opt_out = record['HasOptedOutOfEmail']
            self.adoption_form = record['Has_filled_out_Adoption_Form__c']
            self.contact_id = record['Id']
            self.rover_interest = record['Interested_in_Rover__c']
            self.last_name = record['LastName']
            self.lead_source = record['LeadSource']
            address = record['MailingAddress']
            self.address = (
                address['street'],
                address['city'],
                address.get('stateCode', '') or address['state'],
                address['postalCode'],
                address.get('countryCode', '') or address['country'])
            self.name = record['Name']
            self.newsletter = record['Newsletter_Opt_Out__c']
            self.phone = record['Phone']
            self.position = record['Position__c']
            self.salutation = record['Salutation']
            self.school_type = record['School_Type__c']
            self.school = record['Search_Box__c']
            self.subjects = record['Subject__c']
            self.theme = record['Theme__c']

    class Lead(Record):
        """A Salesforce lead."""

        def __init__(self, record: OrderedDict, **kwargs):
            """Initialize a Salesforce lead record."""
            super(Record, self).__init__(record=record, **kwargs)
            self.adoption_status = record['Adoption_Status__c']
            self.books = record['Book__c']
            self.confirmed = bool(record['Complete__c'])
            self.confirmed_date = record['Confirmed_Date__c']
            self.created_on = record['CreatedDate']
            self.email = record['Email']
            self.faculty_website = record['Faculty_Website__c']
            self.first_name = record['FirstName']
            self.opt_out = record['HasOptedOutOfEmail']
            self.how_did_you_hear = record['How_did_you_Hear__c']
            self.lead_id = record['Id']
            self.last_name = record['LastName']
            self.lead_source = record['LeadSource']
            self.name = record['Name']
            self.newsletter = record['Newsletter_Opt_In__c']
            self.students = int(record['Number_of_Students__c'])
            self.partner_interest = (str(
                record['Partner_Category_Interest__c']).split(';'))
            self.other_partner_interest = record['Partner_Interest_Other__c']
            self.phone = record['Phone']
            self.reject_reason = record['Reject_Reason__c']
            self.role = record['Role__c']
            self.school = record['School__c']
            self.lead_status = record['Status']
            self.subjects = record['Subject__c']
            self.website = record['Website']

    class Organization(Record):
        """A Salesforce organization."""

        def __init__(self, record: OrderedDict, **kwargs):
            """Initialize a Salesforce organization record."""
            super(Record, self).__init__(record=record, **kwargs)
            self.address = (record['BillingStreet'],
                            record['BillingCity'],
                            record['BillingStateCode'],
                            record['BillingPostalCode'])
            self.adoptions = record['Number_of_Adoptions__c']
            self.created = record['CreatedDate']
            self.description = record['Description']
            self.html_name = record['HTML_Name__c']
            self.modified = record['LastModifiedDate']
            self.name = record['Name']
            self.phone = record['Phone']
            self.type = record['Type']
            self.website = record['Website']
