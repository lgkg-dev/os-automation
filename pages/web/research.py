"""The Web research overview page."""

# from time import sleep
#
# from pypom import Region
from selenium.webdriver.common.by import By

from pages.web.base import WebBase


class Research(WebBase):
    """The researchers page."""

    URL_TEMPLATE = '/research'

    _title_locator = (By.TAG_NAME, 'h1')

    @property
    def loaded(self):
        """Override the base loader."""
        return self.find_element(*self._root_locator).is_displayed