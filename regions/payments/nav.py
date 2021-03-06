"""OpenStax payment nav bar region object."""

from pypom import Region
from selenium.webdriver.common.by import By


class PaymentsNav(Region):
    """OpenStax payment nav bar region object."""

    _root_locator = (By.ID, 'header')
    _logo_locator = (By.ID, 'branding')
    _view_site_locator = (By.PARTIAL_LINK_TEXT, 'SITE')
    _log_out_locator = (By.PARTIAL_LINK_TEXT, 'OUT')

    def is_displayed(self):
        """Return True if the navigation bar is visible."""
        return self.find_element(*self._logo_locator).is_displayed()

    def click_logo(self):
        """Click on the logo to return home."""
        self.find_element(*self._logo_locator).click()
        from pages.payments.home import PaymentsHome
        return PaymentsHome(self.driver)

    def log_out(self):
        """Log out of Payments."""
        self.find_element(*self._log_out_locator).click()
        from pages.payments.logout import PaymentsLogOut
        return PaymentsLogOut(self.driver)
