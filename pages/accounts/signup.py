"""Break the signup process out of the base."""

from __future__ import annotations

from time import sleep
from typing import List, Union
from urllib.parse import urlparse

from pypom import Page, Region
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.accounts.base import AccountsBase
from pages.accounts.profile import Profile
from regions.accounts.fields import Email, FirstName, LastName, Password, Phone, Pin  # NOQA
from regions.accounts.social import SocialLogins
from utils.accounts import AccountsException
from utils.email import GmailReader, GuerrillaMail, RestMail
from utils.utilities import Utility, go_to_

ERROR_SELECTOR = ' ~ .errors .invalid-message'


class ChangeYourEmail(AccountsBase):
    """The email change request page."""

    URL_TEMPLATE = '/i/change_your_email'

    class Content(AccountsBase.Content, Email):
        """The email change request pane."""

        _email_locator = (
            By.CSS_SELECTOR, '#change_signup_email_email')
        _information_message_locator = (
            By.CSS_SELECTOR, '.info-message')
        _send_my_pin_button_locator = (
            By.CSS_SELECTOR, '[type=submit]')

        _email_error_message_locator = (
            By.CSS_SELECTOR, _email_locator[1] + ERROR_SELECTOR)

        def send_my_pin(self) -> Union[ChangeYourEmail, ConfirmEmail]:
            """Click the 'Send my PIN' button.

            :return: the change your email page if there was an error or the
                email confirmation page
            :rtype: :py:class:`~pages.accounts.signup.ChangeYourEmail` or
                :py:class:`~pages.accounts.signup.ConfirmEmail`

            """
            button = self.find_element(*self._send_my_pin_button_locator)
            Utility.click_option(self.driver, element=button)
            sleep(0.5)
            if self.email_has_error:
                return self
            return go_to_(
                ConfirmEmail(self.driver, base_url=self.page.base_url))


class CompleteSignup(AccountsBase):
    """The account setup completion page."""

    URL_TEMPLATE = '/i/done'

    class Content(AccountsBase.Content):
        """The signup completion pane."""

        _email_locator = (
            By.CSS_SELECTOR, '.info-message b')
        _exit_button_locator = (
            By.CSS_SELECTOR, '#exit-icon a')
        _finish_button_locator = (
            By.CSS_SELECTOR, '[type=submit]')
        _information_message_locator = (
            By.CSS_SELECTOR, '.info-message')

        @property
        def information(self) -> str:
            """Return the email information message.

            :return: the email information message
            :rtype: str

            """
            return (self.find_element(*self._information_message_locator)
                    .get_attribute('textContent'))

        @property
        def email(self) -> str:
            """Return the email address used during registration.

            :return: the email address used during registration
            :rtype: str

            """
            return self.find_element(*self._email_locator).text

        def exit(self) -> Page:
            """Click the page return 'x' button.

            :return: the user profile or the origination page
            :rtype: :py:class:`~pypom.Page`

            """
            button = self.find_element(*self._exit_button_locator)
            Utility.click_option(self.driver, element=button)
            sleep(0.5)
            if 'profile' in self.current_url:
                return go_to_(
                    Profile(self.driver, base_url=self.page.base_url))
            return Page(self.driver)

        def finish(self) -> Page:
            """Click the 'Finish' button.

            :return: the account profile or the originating page
            :rtype: :py:class:`~pypom.Page`

            """
            button = self.find_element(*self._finish_button_locator)
            Utility.click_option(self.driver, element=button)
            sleep(0.5)
            if 'profile' in self.driver.current_url:
                return go_to_(
                    Profile(self.driver, base_url=self.page.base_url))
            return Page(self.driver)


class ConfirmEmail(AccountsBase):
    """The email confirmation page."""

    URL_TEMPLATE = '/i/confirmation_form'

    class Content(AccountsBase.Content, Pin):
        """The email confirmation pane."""

        _information_message_locator = (
            By.CSS_SELECTOR, '.info-message')
        _email_locator = (
            By.CSS_SELECTOR, '.info-message b')
        _edit_your_email_link_locator = (
            By.CSS_SELECTOR, '.info-message a')
        _pin_locator = (
            By.CSS_SELECTOR, '#confirm_pin')
        _use_a_different_email_link_locator = (
            By.CSS_SELECTOR, '.control-group a')
        _confirm_my_account_button_locator = (
            By.CSS_SELECTOR, '[type=submit]')

        _pin_error_message_locator = (
            By.CSS_SELECTOR, _pin_locator[1] + ERROR_SELECTOR)

        @property
        def email(self) -> str:
            """Return the email address used during registration.

            :return: the email address used during registration
            :rtype: str

            """
            return self.find_element(*self._email_locator).text

        @property
        def information(self) -> str:
            """Return the email information message.

            :return: the email information message
            :rtype: str

            """
            return (self.find_element(*self._information_message_locator)
                    .get_attribute('textContent'))

        @property
        def pin(self) -> str:
            """Return the current PIN value.

            :return: the current pin value
            :rtype: str

            """
            return (self.find_element(*self._pin_locator)
                    .get_attribute('value'))

        @pin.setter
        def pin(self, pin: str):
            """Enter the email verification number.

            :param str pin: the email verification number
            :return: None

            """
            field = self.find_element(*self._pin_locator)
            Utility.clear_field(self.driver, field=field)
            field.send_keys(pin)

        def confirm_my_account(self) \
                -> Union[CompleteSignup, VerifyInstructor]:
            """Click the Continue button.

            :return: the email confirmation (second step) if there are errors
                or the completion page (third step)
            :rtype: :py:class:`~pages.accounts.signup.CompleteSignup`
                or :py:class:`~pages.accounts.signup.VerifyInstructor`
            :raises :py:class:`~utils.accounts.AccountsException`: if an error
                in the form entries is found

            """
            current_page = self.page.location
            button = self.find_element(
                *self._confirm_my_account_button_locator)
            Utility.click_option(self.driver, element=button)
            sleep(0.5)
            if self.driver.current_url == current_page:
                raise AccountsException(
                    self.driver.execute_script(
                        'return document.querySelector(".invalid-message")'
                        '.textContent;'))
            if 'sheerid.com' in self.driver.current_url:
                return go_to_(VerifyInstructor(self.driver))
            return go_to_(
                CompleteSignup(self.driver, base_url=self.page.base_url))

        def edit_your_email(self) -> ChangeYourEmail:
            """Click the 'edit your email' link.

            :return: the change your email page
            :rtype: :py:class:`~pages.accounts.signup.ChangeYourEmail`

            """
            link = self.find_element(*self._edit_your_email_link_locator)
            Utility.click_option(self.driver, element=link)
            return go_to_(
                ChangeYourEmail(self.driver, base_url=self.page.base_url))

        def sign_up_with_a_different_email(self) -> ChangeYourEmail:
            """Click the 'sign up with a different email' link.

            :return: the change your email page
            :rtype: :py:class:`~pages.accounts.signup.ChangeYourEmail`

            """
            link = self.find_element(*self._use_a_different_email_link_locator)
            Utility.click_option(self.driver, element=link)
            return go_to_(
                ChangeYourEmail(self.driver, base_url=self.page.base_url))


class EducatorSignup(AccountsBase):
    """The educator sign up process."""

    URL_TEMPLATE = '/i/signup/educator'

    def sign_up(self,
                first: str, last: str, email: RestMail, password: str,
                phone: str, school: str,
                page: Page = None, base_url: str = None) \
            -> Page:
        """Register a new educator account.

        :param str first: the instructor's first name
        :param str last: the instructor's last name
        :param RestMail email: the instructor's accessible email address
        :param str password: the new account password
        :param str phone: the instructor's telephone number
        :param Page page: (optional) the expected destination page
        :param str base_url: (optional) the destination page base URL address
        :return: the new account profile if a destination page isn't provided
            or the destination page
        :rtype: :py:class:`~pypom.Page`

        """
        form = self.content
        form.first_name = first
        form.last_name = last
        form.phone = phone
        form.email = email.address
        form.password = password
        form.i_agree()
        if not email.address.endswith('.edu'):
            form._continue()
        confirm_email = form._continue().content

        pin = email.wait_for_mail()[-1].pin
        confirm_email.pin = pin
        instructor_access = confirm_email.confirm_my_account()

        if not instructor_access.location.endswith('/i/done'):
            instructor_access.school_name = school
            validated = instructor_access.verify_my_instructor_status()
            your_done = validated._continue().content
        else:
            your_done = instructor_access.content
        your_done.finish()

        if page:
            return go_to_(page(self.driver, base_url=base_url))
        return go_to_(Profile(self.driver, base_url=self.base_url))

        def get_errors(self) -> List[str]:
            """Return a list of error messages found on the page.

            :return: the list of error messages found on the current page
            :rtype: list(str)

            """
            errors = []
            if self.first_name_has_error:
                errors.append(f'First Name: {self.first_name_error}')
            if self.last_name_has_error:
                errors.append(f'Last Name: {self.last_name_error}')
            if self.email_has_error:
                errors.append(f'Email: {self.email_error}')
            if self.password_has_error:
                errors.append(f'Password: {self.password_error}')
            return errors

    class Content(AccountsBase.Content,
                  Email, FirstName, LastName, Password, Phone):
        """The sign up pane."""

        _continue_button_locator = (
            By.CSS_SELECTOR, '[type=submit]')
        _email_locator = (
            By.CSS_SELECTOR, '#signup_email')
        _first_name_locator = (
            By.CSS_SELECTOR, '#signup_first_name')
        _last_name_locator = (
            By.CSS_SELECTOR, '#signup_last_name')
        _newsletter_signup_locator = (
            By.CSS_SELECTOR, '#signup_newsletter')
        _password_locator = (
            By.CSS_SELECTOR, '#signup_password')
        _phone_locator = (
            By.CSS_SELECTOR, '#signup_phone_number')
        _policy_agreement_locator = (
            By.CSS_SELECTOR, '#signup_terms_accepted')
        _privacy_policy_link_locator = (
            By.CSS_SELECTOR, '.terms [href*=terms]:last-child')
        _show_password_toggle_locator = (
            By.CSS_SELECTOR, '#show-hide-button')
        _terms_of_use_link_locator = (
            By.CSS_SELECTOR, '.terms [href*=terms]:first-child')

        _email_error_message_locator = (
            By.CSS_SELECTOR, _email_locator[1] + ERROR_SELECTOR)
        _first_name_error_message_locator = (
            By.CSS_SELECTOR, _first_name_locator[1] + ERROR_SELECTOR)
        _last_name_error_message_locator = (
            By.CSS_SELECTOR, _last_name_locator[1] + ERROR_SELECTOR)
        _password_error_message_locator = (
            By.CSS_SELECTOR, _password_locator[1] + ERROR_SELECTOR)
        _phone_error_message_locator = (
            By.CSS_SELECTOR, _phone_locator[1] + ERROR_SELECTOR)

        def i_agree(self) -> StudentSignup:
            """Click the I agree checkbox.

            :return: the Accounts student sign up page
            :rtype: :py:class:`~pages.accounts.signup.StudentSignup`

            """
            checkbox = self.find_element(*self._policy_agreement_locator)
            Utility.click_option(self.driver, element=checkbox)
            return self.page

        def toggle_newsletter(self) -> StudentSignup:
            """Click the OpenStax newsletter checkbox.

            :return: the Accounts student sign up page
            :rtype: :py:class:`~pages.accounts.signup.StudentSignup`

            """
            checkbox = self.find_element(*self._newsletter_signup_locator)
            Utility.click_option(self.driver, element=checkbox)
            return self.page

        def toggle_password_display(self) -> StudentSignup:
            """Toggle the password field to show or hide the value.

            :return: the Accounts student sign up page
            :rtype: :py:class:`~pages.accounts.signup.StudentSignup`

            """
            toggle = self.find_element(*self._show_password_toggle_locator)
            Utility.click_option(self.driver, element=toggle)
            sleep(0.1)
            return self.page

        def _continue(self) -> Union[StudentSignup, ConfirmEmail]:
            """Click the Continue button.

            :param Page previous: (optional) the Page object for the initial
                page that sent the log in request
            :param str base_url: (optional) the base URL for the previous Page
            :param kwargs: (optional) additional keyword arguments for the Page
            :return: the student sign up (first step) if there are errors or
                the email confirmation (second step)
            :rtype: :py:class:`~pages.accounts.signup.StudentSignup` or
                :py:class:`~pages.accounts.signup.ConfirmEmail`

            """
            current_page = self.page.location
            button = self.find_element(*self._continue_button_locator)
            Utility.click_option(self.driver, element=button)
            sleep(0.5)
            if self.driver.current_url == current_page:
                error = self.driver.execute_script(
                    'return document.querySelector(".invalid-message");')
                if error:
                    raise AccountsException(error.get_attribute('textContent'))
            return go_to_(
                ConfirmEmail(self.driver, base_url=self.page.base_url))


class Signup(AccountsBase):
    """The Accounts sign up process."""

    URL_TEMPLATE = '/i/signup'

    class Content(AccountsBase.Content):
        """The sign up pane."""

        DESCRIPTION = ' ~ div'

        _educator_signup_button_locator = (
            By.CSS_SELECTOR, '[href$=educator]')
        _student_signup_button_locator = (
            By.CSS_SELECTOR, '[href$=student]')

        _educator_descrition_locator = (
            By.CSS_SELECTOR, _educator_signup_button_locator[1] + DESCRIPTION)
        _student_description_locator = (
            By.CSS_SELECTOR, _student_signup_button_locator[1] + DESCRIPTION)

        @property
        def educator_description(self) -> str:
            """Return the educator sign up explanation text.

            :return: the explanation why educators should register for an
                OpenStax account
            :rtype: str

            """
            return (self.find_element(*self._educator_descrition_locator)
                    .get_attribute('textContent'))

        @property
        def student_description(self) -> str:
            """Return the student sign up explanation text.

            :return: the explanation why students should register for an
                OpenStax account
            :rtype: str

            """
            return (self.find_element(*self._student_description_locator)
                    .get_attribute('textContent'))

        def sign_up_as_an_educator(self) -> EducatorSignup:
            """Click the educator sign up button.

            :return: the educator registration process
            :rtype: :py:class:`~pages.accounts.signup.EducatorSignup`

            """
            button = self.find_element(*self._educator_signup_button_locator)
            Utility.click_option(self.driver, element=button)
            return go_to_(
                EducatorSignup(self.driver, base_url=self.page.base_url))

        def sign_up_as_a_student(self) -> StudentSignup:
            """Click the student sign up button.

            :return: the student registration process
            :rtype: :py:class:`~pages.accounts.signup.StudentSignup`

            """
            button = self.find_element(*self._student_signup_button_locator)
            Utility.click_option(self.driver, element=button)
            return go_to_(
                StudentSignup(self.driver, base_url=self.page.base_url))


class StudentSignup(AccountsBase):
    """The student sign up process."""

    URL_TEMPLATE = '/i/signup/student'

    def sign_up(self,
                first: str, last: str, email: RestMail, password: str,
                page: Page = None, base_url: str = None) \
            -> Page:
        """Register a new student account.

        :param str first: the student's first name
        :param str last: the student's last name
        :param RestMail email: the student's accessible email address
        :param str password: the new account password
        :param Page page: (optional) the expected destination page
        :param str base_url: (optional) the destination page base URL address
        :return: the new account profile if a destination page isn't provided
            or the destination page
        :rtype: :py:class:`~pypom.Page`

        """
        form = self.content
        form.first_name = first
        form.last_name = last
        form.email = email.address
        form.password = password
        form.i_agree()
        confirm_email = form._continue().content
        pin = email.wait_for_mail()[-1].pin
        confirm_email.pin = pin
        complete_sign_up = confirm_email.confirm_my_account().content
        complete_sign_up.finish()
        if page:
            return go_to_(page(self.driver, base_url=base_url))
        return go_to_(Profile(self.driver, base_url=self.base_url))

    class Content(AccountsBase.Content,
                  Email, FirstName, LastName, Password, SocialLogins):
        """The sign up pane."""

        _continue_button_locator = (
            By.CSS_SELECTOR, '[type=submit]')
        _email_locator = (
            By.CSS_SELECTOR, '#signup_email')
        _first_name_locator = (
            By.CSS_SELECTOR, '#signup_first_name')
        _last_name_locator = (
            By.CSS_SELECTOR, '#signup_last_name')
        _newsletter_signup_locator = (
            By.CSS_SELECTOR, '#signup_newsletter')
        _password_locator = (
            By.CSS_SELECTOR, '#signup_password')
        _policy_agreement_locator = (
            By.CSS_SELECTOR, '#signup_terms_accepted')
        _privacy_policy_link_locator = (
            By.CSS_SELECTOR, '.terms [href*=terms]:last-child')
        _show_password_toggle_locator = (
            By.CSS_SELECTOR, '#show-hide-button')
        _terms_of_use_link_locator = (
            By.CSS_SELECTOR, '.terms [href*=terms]:first-child')

        _email_error_message_locator = (
            By.CSS_SELECTOR, _email_locator[1] + ERROR_SELECTOR)
        _first_name_error_message_locator = (
            By.CSS_SELECTOR, _first_name_locator[1] + ERROR_SELECTOR)
        _last_name_error_message_locator = (
            By.CSS_SELECTOR, _last_name_locator[1] + ERROR_SELECTOR)
        _password_error_message_locator = (
            By.CSS_SELECTOR, _password_locator[1] + ERROR_SELECTOR)

        def get_errors(self) -> List[str]:
            """Return a list of error messages found on the page.

            :return: the list of error messages found on the current page
            :rtype: list(str)

            """
            errors = []
            if self.first_name_has_error:
                errors.append(f'First Name: {self.first_name_error}')
            if self.last_name_has_error:
                errors.append(f'Last Name: {self.last_name_error}')
            if self.email_has_error:
                errors.append(f'Email: {self.email_error}')
            if self.password_has_error:
                errors.append(f'Password: {self.password_error}')
            return errors

        def i_agree(self) -> StudentSignup:
            """Click the I agree checkbox.

            :return: the Accounts student sign up page
            :rtype: :py:class:`~pages.accounts.signup.StudentSignup`

            """
            checkbox = self.find_element(*self._policy_agreement_locator)
            Utility.click_option(self.driver, element=checkbox)
            return self.page

        def toggle_newsletter(self) -> StudentSignup:
            """Click the OpenStax newsletter checkbox.

            :return: the Accounts student sign up page
            :rtype: :py:class:`~pages.accounts.signup.StudentSignup`

            """
            checkbox = self.find_element(*self._newsletter_signup_locator)
            Utility.click_option(self.driver, element=checkbox)
            return self.page

        def toggle_password_display(self) -> StudentSignup:
            """Toggle the password field to show or hide the value.

            :return: the Accounts student sign up page
            :rtype: :py:class:`~pages.accounts.signup.StudentSignup`

            """
            toggle = self.find_element(*self._show_password_toggle_locator)
            Utility.click_option(self.driver, element=toggle)
            sleep(0.1)
            return self.page

        def _continue(self) -> Union[StudentSignup, ConfirmEmail]:
            """Click the Continue button.

            :param Page previous: (optional) the Page object for the initial
                page that sent the log in request
            :param str base_url: (optional) the base URL for the previous Page
            :param kwargs: (optional) additional keyword arguments for the Page
            :return: the student sign up (first step) if there are errors or
                the email confirmation (second step)
            :rtype: :py:class:`~pages.accounts.signup.StudentSignup` or
                :py:class:`~pages.accounts.signup.ConfirmEmail`

            """
            current_page = self.page.location
            button = self.find_element(*self._continue_button_locator)
            Utility.click_option(self.driver, element=button)
            sleep(0.5)
            if self.driver.current_url == current_page:
                raise AccountsException(
                    self.driver.execute_script(
                        'return document.querySelector(".invalid-message")'
                        '.textContent;'))
            return go_to_(
                ConfirmEmail(self.driver, base_url=self.page.base_url))


class SuccessfulVerification(Page):
    """The successful verification page."""

    _continue_button_locator = (
        By.CSS_SELECTOR, '.sid-btn')

    def _continue(self) -> CompleteSignup:
        """Click the Continue button.

        :return: the account creation completion page
        :rtype: :py:class:`~pages.accounts.signup.CompleteSignup`

        """
        button = self.find_element(*self._continue_button_locator)
        Utility.click_option(self.driver, element=button)
        return go_to_(CompleteSignup(self.driver))


class VerifyInstructor(Page):
    """The SheerID instructor verification form."""

    _country_selection_locator = (
        By.CSS_SELECTOR, '#sid-country')
    _email_locator = (
        By.CSS_SELECTOR, '#sid-email')
    _first_name_locator = (
        By.CSS_SELECTOR, '#sid-first-name')
    _last_name_locator = (
        By.CSS_SELECTOR, '#sid-last-name')
    _school_name_locator = (
        By.CSS_SELECTOR, '#sid-teacher-school')
    _verify_my_instructor_status_button_locator = (
        By.CSS_SELECTOR, '[type=submit]')

    @property
    def email(self) -> str:
        """Return the sign up email address.

        :return: the email used during sign up
        :rtype: str

        """
        return self.find_element(*self._email_locator).text

    @property
    def country(self) -> str:
        """Return the currently selected country.

        :return: the currently selected country
        :rtype: str

        """
        return (self.find_element(*self._country_selection_locator)
                .get_attribute('value'))

    @country.setter
    def country(self, country: str = 'United States'):
        """Set the user's country.

        :param str country: the country name
        :return: None

        """
        self.find_element(*self._country_selection_locator).send_keys(country)


""" *********************************************************************** """


class SignupOld(AccountsBase):
    """Legacy signup process."""

    URL_TEMPLATE = '/signup'

    STUDENT = 'Student'
    INSTRUCTOR = 'Instructor'
    ADMINISTRATOR = 'Administrator'
    LIBRARIAN = 'Librarian'
    DESIGNER = 'Instructional Designer'
    OTHER = 'Other'

    GOOGLE = 'google'
    GUERRILLA_MAIL = 'guerrilla'
    RESTMAIL = 'restmail'

    TITLE = 0
    FIRST = 1
    LAST = 2
    SUFFIX = 3

    ADOPTED = 'Fully adopted and using it as the primary textbook'
    RECOMMENDED = 'Recommending the book – my students buy a different book'
    INTEREST = 'Interested in using OpenStax in the future'
    NOT_USING = 'Not using OpenStax'

    SUBJECTS = [
        ('accounting', 'Accounting'),
        ('algebra_and_trigonometry', 'Algebra and Trigonometry'),
        ('american_government', 'American Government'),
        ('anatomy_physiology', 'Anatomy and Physiology'),
        ('astronomy', 'Astronomy'),
        ('biology', 'Biology'),
        ('calculus', 'Calculus'),
        ('chemistry', 'Chemistry'),
        ('chem_atoms_first', 'Chemistry: Atoms First'),
        ('college_algebra', 'College Algebra'),
        ('college_physics_algebra', 'College Physics'),
        ('concepts_of_bio_non_majors', 'Concepts of Biology'),
        ('introduction_to_business', 'Introduction to Business'),
        ('introduction_to_sociology', 'Introduction to Sociology 2e'),
        ('introductory_statistics', 'Introductory Statistics'),
        ('microbiology', 'Microbiology'),
        ('pre_algebra', 'Prealgebra'),
        ('precalc', 'Precalculus'),
        ('economics', 'Principles of Economics'),
        ('macro_econ', 'Principles of Macroeconomics'),
        ('ap_macro_econ', 'Principles of Macroeconomics for AP® Courses'),
        ('micro_econ', 'Principles of Microeconomics'),
        ('ap_micro_econ', 'Principles of Microeconomics for AP® Courses'),
        ('psychology', 'Psychology'),
        ('ap_physics', 'The AP Physics Collection'),
        ('us_history', 'U.S. History'),
        ('university_physics_calc', 'University Physics'),
        ('not_listed', 'Not Listed')
    ]

    _next_button_locator = (By.CSS_SELECTOR, '[type=submit]')
    _next_page_button_locator = (
                            By.CSS_SELECTOR, '[data-bind="click:nextPage"]')
    _form_submit_locator = (By.CSS_SELECTOR, '[value="Create Account"]')
    _error_locator = (By.CSS_SELECTOR, '.alert')

    def subject_list(self, size=1):
        """Return a list of subjects for an elevated signup."""
        subjects = len(self.SUBJECTS)
        if size > subjects:
            size = subjects
        book = ''
        group = []
        while len(group) < size:
            book = (self.SUBJECTS[Utility.random(0, subjects - 1)])[1]
            if book not in group:
                group.append(book)
        return group

    def account_signup(self, email,
                       password=None, _type='Student', provider='restmail',
                       tutor=False, destination=None,
                       **kwargs):
        r"""Single signup entry point.

        Sign up a new user. Social, Random, and Name are mutually exclusive.

        :param str email: an accessible e-mail address
        :param str password: the user password
        :param str _type: (optional) the new user account type using
            * :py:data:`SignupOld.STUDENT` (default)
            * :py:data:`SignupOld.INSTRUCTOR`
            * :py:data:`SignupOld.ADMINISTRATOR`
            * :py:data:`SignupOld.LIBRARIAN`
            * :py:data:`SignupOld.DESIGNER`
            * :py:data:`SignupOld.OTHER`
        :param str provider: (optional) the e-mail host, default: ``restmail``
            ``google``: Google Gmail
            ``guerrilla``: GuerrillaMail
            ``restmail``: RestMail API Email
        :param bool tutor: (optional) ``True`` if the signup is for OpenStax
            Tutor, default: ``False``
        :param str destination: a URL destination if not Accounts
            default: ``None``
        :param \**kwarys: arbitrary keyword arguments, see below
        :return: the new user's profile page
        :rtype: :py:class:`pages.accounts.profile.Profile`

        :Keyword Arguments:
            * *email_password* (``str``) --
              Webmail login password
            * *name* (``list``(``str``)) --
              the user's name as [title, first_name, last_name, suffix]
            * *news* (``bool``) --
              ``True`` if the newsletter checkbox should be checked, ``False``
              if the checkbox should be cleared
            * *phone* (``str``) --
              the instructor's telephone number
            * *school* (``str``) --
              the school name
            * *social* (``str``) --
              use a social login, either ``facebook`` or ``google``
            * *social_login* (``str``) --
              the social account login
            * *social_password* (``str``) --
              the social account password
            * *students* (``int``) --
              the number of students in the course
            * *subjects* (``list``(``str``)) --
              a list of interested book subjects
              * ``accounting``
              * ``algebra_and_trigonometry``
              * ``american_government``
              * ``anatomy_physiology``
              * ``astronomy``
              * ``biology``
              * ``calculus``
              * ``chemistry``
              * ``chem_atoms_first``
              * ``college_algebra``
              * ``college_physics_algebra``
              * ``concepts_of_bio_non_majors``
              * ``introduction_to_business``
              * ``introduction_to_sociology``
              * ``introductory_statistics``
              * ``microbiology``
              * ``pre_algebra``
              * ``precalc``
              * ``economics``
              * ``macro_econ``
              * ``ap_macro_econ``
              * ``micro_econ``
              * ``ap_micro_econ``
              * ``psychology``
              * ``ap_physics``
              * ``us_history``
              * ``university_physics_calc``
              * ``not_listed``
            * *use* (``str``) --
              How is the instructor using OpenStax?

              * :py:data:`SignupOld.ADOPTED` --
                  'Fully adopted and using it as the primary textbook'
              * :py:data:`SignupOld.RECOMMENDED` --
                  'Recommending the book - my students buy a different book'
              * :py:data:`SignupOld.INTEREST` --
                  'Interested in using OpenStax in the future'
              * :py:data:`SignupOld.NOT_USING` --
                  'Not using OpenStax'
            * *webpage* (``str``) --
              the web URL showing the user as a known instructor

        """
        # prep the signup help
        if 'kwargs' in kwargs:
            kwargs = kwargs.get('kwargs')
        non_student_role = _type != SignupOld.STUDENT
        instructor = _type == SignupOld.INSTRUCTOR

        # select user type and email
        if not tutor:
            self.user_type.role = _type
        self.user_type.email = email
        self.next()
        sleep(0.5)
        assert(not self.error), '{0}'.format(self.error)
        if non_student_role and not email.endswith('edu'):
            self.next()

        # verify the pin
        not_verified = True
        while not_verified:
            email_password = None
            if 'google' in provider:
                # mailer = GoogleBase(self.driver)
                pin = (GmailReader(email[0:7])
                       .read_mail()
                       .sort_mail()
                       .latest
                       .get_pin)
                email_password = kwargs.get('email_password')
            elif 'guerrilla' in provider:
                mailer = GuerrillaMail(self.driver)
            elif 'restmail' in provider:
                account_name = email[:email.rfind("@")]
                mailer = RestMail(account_name)
            else:
                mailer = _type(self.driver)
                email_password = kwargs.get('email_password')
            if 'google' not in provider:
                pin = self._get_pin(page=mailer,
                                    provider=provider,
                                    return_url=(self.seed_url +
                                                '/verify_email'),
                                    email=email,
                                    password=email_password)
            if not pin:
                raise ValueError('PIN not found')
            self.pin.clear_pin()
            self.pin.verify_pin = pin
            self.next()
            sleep(0.25)
            if not self.pin.pin_failure:
                not_verified = False

        sleep(1.0)
        if 'social' not in kwargs:
            # set the initial password
            self.password.password = password
            self.password.confirmation = password
            sleep(0.5)
            self.next()
            assert(not self.error), '{0}'.format(self.error)
            self.wait.until(lambda _: 'profile' in self.location)
        elif kwargs.get('social') == 'facebook':
            # use Facebook
            self.password.use_social_login() \
                .use_facebook.log_in(kwargs.get('social_login'),
                                     kwargs.get('social_password'))
            sleep(3.0)
        else:
            # use Google
            self.password.use_social_login() \
                .use_google.log_in(kwargs.get('social_login'),
                                   kwargs.get('social_password'))
            sleep(3.0)

        # make sure we're actually back on Accounts
        self.wait.until(
            lambda _: 'accounts' in urlparse(self.selenium.current_url).netloc)
        sleep(1.0)
        # enter user details in group order
        # all users
        if 'social' not in kwargs:
            self.user.first_name = kwargs.get('name')[SignupOld.FIRST]
            self.user.last_name = kwargs.get('name')[SignupOld.LAST]
            self.user.suffix = kwargs.get('name')[SignupOld.SUFFIX]
        if non_student_role:
            self.instructor.phone = kwargs.get('phone')
        self.user.school = kwargs.get('school')
        if instructor:
            self.instructor.students = kwargs.get('students')
        if non_student_role:
            self.instructor.webpage = kwargs.get('webpage')
        # instructor-only
        if instructor:
            # from utils.accounts import Accounts
            self.instructor.using = kwargs.get('use')
            '''self.instructor.using = [
                Accounts.NOT_USING,
                Accounts.ADOPTED
            ][Utility.random(0, 1)]'''
            sleep(0.25)
        # self.next((By.CSS_SELECTOR, '[data-bind~="click:nextPage"]'))
        '''if not non_student_role:
            self.next()'''
        # completion
        # sleep(1)
        subjects_to_select = []
        if non_student_role:
            for _, name in SignupOld.SUBJECTS:
                if name in kwargs.get('subjects', []):
                    subjects_to_select.append(name)
        if subjects_to_select:
            self.instructor.select_subjects(subjects_to_select)
            '''for subject in subjects_to_select:
                book = self.find_element(
                    By.XPATH,
                    '//label[text()="{subject}"]/following-sibling::div'
                    .format(subject=subject))
                Utility.click_option(self.driver, element=book)'''
        '''if instructor:
            if kwargs.get('use') == Accounts.NOT_USING:
                self.instructor.students = kwargs.get('students')
            else:
                for group in self.find_elements(
                        By.CSS_SELECTOR, '.form-group input[type=number]'):
                    Utility.scroll_to(self.driver, element=group, shift=-80)
                    group.send_keys(kwargs.get('students'))
                radios = self.find_elements(
                    By.CSS_SELECTOR,
                    '.form-group div input[data-bind*="how_using"]')
                group = zip(radios[0::2], radios[1::2])
                for adopted, recommend in group:
                    if kwargs.get('use') == Accounts.ADOPTED:
                        option = adopted
                    else:
                        option = recommend
                    Utility.click_option(self.driver, element=option)
        '''
        if not kwargs.get('news'):
            self.user.toggle_news()
        if not tutor:
            self.user.agree_to_terms()
        sleep(0.25)
        self.next()
        if non_student_role:
            assert(not self.error), '{0}'.format(self.error)

        # request e-mail confirmation for an elevated account
        if non_student_role:
            self.notice.get_confirmation_email()
            self.next()

        if tutor:
            from pages.tutor.enrollment import Terms
            return go_to_(
                Terms(self.driver,
                      base_url=destination if destination else None))

        # if an alternative destination Page is provided (like from Web), wait
        # for it to be loaded
        if isinstance(destination, Page):
            return go_to_(destination)

        from pages.accounts.profile import Profile
        return go_to_(Profile(self.driver, base_url=self.base_url))

    def instructor_access(self, role, school_email, phone_number, school,
                          webpage, students=None, using=None, interests=None,
                          get_newsletter=True):
        """Request faculty access."""
        _apply_role_locator = (By.CSS_SELECTOR, '#apply_role')
        _apply_email_locator = (By.CSS_SELECTOR, '#apply_email')
        _apply_phone_locator = (By.CSS_SELECTOR, '#apply_phone_number')
        _apply_school_locator = (By.CSS_SELECTOR, '#apply_school')
        _apply_student_locator = (By.CSS_SELECTOR, '#apply_num_students')
        _apply_url_locator = (By.CSS_SELECTOR, '#apply_url')
        _apply_using_locator = (By.CSS_SELECTOR, '#apply_using_openstax')
        _apply_subject_locators = (By.CSS_SELECTOR, '.subject')
        _subject_label_locator = (By.CSS_SELECTOR, 'label')
        _subject_checkbox_locator = (By.CSS_SELECTOR, '[type=checkbox]')
        _apply_newsletter_locator = (By.CSS_SELECTOR, '#apply_newsletter')

        Utility.select(self.driver, _apply_role_locator, role)
        _email = self.find_element(*_apply_email_locator)
        Utility.scroll_to(self.driver, element=_email)
        _email.send_keys(school_email)
        _phone = self.find_element(*_apply_phone_locator)
        Utility.scroll_to(self.driver, element=_phone)
        _phone.send_keys(phone_number)
        _school = self.find_element(*_apply_school_locator)
        Utility.scroll_to(self.driver, element=_school)
        _school.send_keys(school)
        if role == self.INSTRUCTOR:
            _students = self.find_element(*_apply_student_locator)
            Utility.scroll_to(self.driver, element=_students)
            _students.send_keys(students)
        _webpage = self.find_element(*_apply_url_locator)
        Utility.scroll_to(self.driver, element=_webpage)
        _webpage.send_keys(webpage)
        if role == self.INSTRUCTOR:
            Utility.select(self.driver, _apply_using_locator, using)
        books = self.find_elements(*_apply_subject_locators)
        if not interests:
            interests = self.subject_list(Utility.random(1, 5))
        for book in books:
            if book.find_element(*_subject_label_locator).text in interests:
                _book = book.find_element(*_subject_checkbox_locator)
                Utility.click_option(self.driver, element=_book)
        _news = self.find_element(*_apply_newsletter_locator)
        Utility.scroll_to(self.driver, element=_news)
        if not get_newsletter:
            Utility.click_option(self.driver, element=_news)
        self.next()
        sleep(1.0)
        self.notice.get_confirmation_email()
        self.next()

    @property
    def user_type(self):
        """Fill out the user type."""
        return self.UserType(self)

    @property
    def pin(self):
        """Verify the e-mail pin."""
        return self.PinVerification(self)

    def _get_pin(self, page, provider, return_url, email=None, password=None):
        """Retrieve a signup pin."""
        if 'restmail' in provider:
            box = page.wait_for_mail()
            return box[-1].pin
        else:
            page.open()
            if 'google' in provider:
                page = page.login.go(email, password)
            WebDriverWait(page.driver, 60.0).until(
                lambda _: page.emails[0].has_pin and page.emails[0].is_new)
            sleep(5.0)
            pin = page.emails[0].get_pin
            page.driver.get(return_url)
            sleep(1.0)
        return pin

    @property
    def password(self):
        """Fill out the password fields."""
        return self.SetPassword(self)

    @property
    def social(self):
        """Use a social login."""
        return self.SocialLogin(self)

    @property
    def user(self):
        """Fill out the user data."""
        return self.UserFields(self)

    @property
    def instructor(self):
        """Fill out the instructor verification."""
        return self.InstructorVerification(self)

    @property
    def notice(self):
        """Request notice when instructor access is authorized."""
        return self.InstructorNotice(self)

    def next(self, locator=None):
        """Proceed to the next step in the process."""
        if not locator:
            locator = self._next_button_locator
        button = self.find_element(*locator)
        Utility.click_option(self.driver, element=button)
        return self

    @property
    def error(self):
        """Return the error message if present."""
        try:
            return self.find_element(*self._error_locator).text.strip()
        except WebDriverException:
            return ''

    class UserType(Region):
        """Initial signup pane for type selection."""

        _signup_role_locator = (By.ID, 'signup_role')
        _signup_email_locator = (By.ID, 'signup_email')
        _warning_locator = (By.CLASS_NAME, 'warning')
        _sign_in_locator = (By.CSS_SELECTOR, '.sign-in a')

        @property
        def role(self):
            """Return the role select."""
            return self.find_element(*self._signup_role_locator)

        @role.setter
        def role(self, signup_role):
            """Select a user role."""
            Utility.select(self.driver, self._signup_role_locator, signup_role)
            return self

        @property
        def email(self):
            """Return the email input."""
            return self.find_element(*self._signup_email_locator)

        @email.setter
        def email(self, email):
            """Send the e-mail."""
            self.email.send_keys(email)
            return self

        @property
        def warning(self):
            """Return the warning text."""
            return self.find_element(*self._warning_locator).text

        @property
        def warning_present(self):
            """Return True if the e-mail warning is displayed."""
            return self.find_element(*self._warning_locator).is_displayed()

        def log_in(self):
            """Return to the login screen."""
            sign_in = self.find_element(*self._sign_in_locator)
            Utility.click_option(self.driver, element=sign_in)
            from pages.accounts.home import AccountsHome
            return go_to_(
                AccountsHome(self.driver, base_url=self.page.base_url))

    class PinVerification(Region):
        """Pin verification."""

        _pin_locator = (By.ID, 'pin_pin')
        _email_edit_locator = (By.CSS_SELECTOR, '.extra-info a')
        _error_locator = (By.CLASS_NAME, 'alert-danger')

        @property
        def verify_pin(self):
            """Return the pin input."""
            return self.find_element(*self._pin_locator)

        @verify_pin.setter
        def verify_pin(self, pin):
            """Send the verification code."""
            self.verify_pin.send_keys(pin)
            return self

        def edit_email(self):
            """Return to the user type selection."""
            edit_email = self.find_element(*self._email_edit_locator)
            Utility.click_option(self.driver, element=edit_email)
            return self.UserType(self)

        @property
        def pin_failure(self):
            """Return True if an error occurs during pin verification."""
            try:
                WebDriverWait(self.selenium, 1).until(
                    lambda _: self.find_element(*self._error_locator))
            except TimeoutException:
                return False
            return True

        def clear_pin(self):
            """Clear the pin field for Chrome and Firefox."""
            Utility.clear_field(self.selenium, self.verify_pin)

    class SetPassword(Region):
        """Set the user's password."""

        _password_locator = (By.ID, 'signup_password')
        _password_confirmation_locator = (
            By.ID, 'signup_password_confirmation')
        _error_locator = (By.CLASS_NAME, 'alert')
        _multi_error_locator = (By.CSS_SELECTOR, '.alert li')
        _go_to_social_locator = (By.CSS_SELECTOR, '[href$=social]')

        @property
        def password(self):
            """Return the password field."""
            return self.find_element(*self._password_locator)

        @password.setter
        def password(self, password):
            """Set the password."""
            self.find_element(*self._password_locator).send_keys(password)
            return self

        @property
        def confirmation(self):
            """Return the confirmation field."""
            return self.find_element(*self._password_confirmation_locator)

        @confirmation.setter
        def confirmation(self, password):
            """Set the password confirmation."""
            self.confirmation.send_keys(password)
            return self

        @property
        def has_error(self):
            """Return True if error messages are displayed."""
            return bool(self.find_elements(*self._error_locator))

        @property
        def get_error(self):
            """Return password error(s)."""
            if not self.has_error:
                return []
            try:
                return [el.text for el in
                        self.find_elements(*self._multi_error_locator)]
            except Exception:
                return [self.find_element(*self._error_locator).text]

        def use_social_login(self):
            """Go to the social login setup."""
            use_social = self.find_element(*self._go_to_social_locator)
            Utility.click_option(self.driver, element=use_social)
            return SignupOld.SocialLogin(self)

    class UserFields(Region):
        """Standard user fields."""

        _first_name_locator = (By.ID, 'profile_first_name')
        _last_name_locator = (By.ID, 'profile_last_name')
        _school_locator = (By.ID, 'profile_school')
        _news_locator = (By.ID, 'profile_newsletter')
        _policy_agreement_locator = (By.ID, 'profile_i_agree')

        @property
        def first_name(self):
            """Return the first name field."""
            return self.find_element(*self._first_name_locator)

        @first_name.setter
        def first_name(self, first):
            """Send the user's first name."""
            self.first_name.send_keys(first)
            return self

        @property
        def last_name(self):
            """Return the surname field."""
            return self.find_element(*self._last_name_locator)

        @last_name.setter
        def last_name(self, last):
            """Send the user's surname."""
            self.last_name.send_keys(last)
            return self

        @property
        def school(self):
            """Return the school field."""
            return self.find_element(*self._school_locator)

        @school.setter
        def school(self, school):
            """Send the user's school or affiliation."""
            self.school.send_keys(school)
            return self

        def toggle_news(self):
            """Toggle between receiving and not receiving news."""
            news = self.find_element(*self._news_locator)
            Utility.click_option(self.driver, element=news)
            return self

        def agree_to_terms(self):
            """Accept the Accounts terms of use and the privacy policy."""
            accept_terms = self.find_element(*self._policy_agreement_locator)
            Utility.click_option(self.driver, element=accept_terms)
            return self

    class SocialLogin(Region):
        """Sign up using a social app profile."""

        URL_TEMPLATE = '/social'

        _facebook_button_locator = (By.ID, 'facebook-login-button')
        _google_button_locator = (By.ID, 'google-login-button')
        _go_to_password_setup_locator = (By.CSS_SELECTOR, '[href$=password]')

        @property
        def use_facebook(self):
            """Use Facebook to log in."""
            fb_login = self.find_element(*self._facebook_button_locator)
            Utility.click_option(self.driver, element=fb_login)
            from pages.facebook.home import Facebook
            return Facebook(self.driver)

        @property
        def use_google(self):
            """Use Google to log in."""
            g_login = self.find_element(*self._google_button_locator)
            Utility.click_option(self.driver, element=g_login)
            from pages.google.home import Google
            return Google(self.driver)

        @property
        def use_a_password(self):
            """Use a non-social log in."""
            non_social = self.find_element(*self._go_to_password_setup_locator)
            Utility.click_option(self.driver, element=non_social)
            return SignupOld.SetPassword(self)

    class InstructorVerification(Region):
        """Instructor verification fields."""

        _phone_locator = (By.ID, 'profile_phone_number')
        _student_number_locator = (By.ID, 'profile_num_students')
        _webpage_verification_locator = (By.ID, 'profile_url')
        _using_openstax_locator = (By.ID, 'profile_using_openstax')
        _subject_option_locator = (By.CLASS_NAME, 'subject')

        @property
        def phone(self):
            """Return the telephone number field."""
            return self.find_element(*self._phone_locator)

        @phone.setter
        def phone(self, phone_number):
            """Send the verification telephone number."""
            self.phone.send_keys(phone_number)
            return self

        @property
        def students(self):
            """Return the student count field."""
            return self.find_element(*self._student_number_locator)

        @students.setter
        def students(self, students):
            """Send the semester course student count."""
            self.students.send_keys(str(students))
            return self

        @property
        def webpage(self):
            """Return the webpage verification field."""
            return self.find_element(*self._webpage_verification_locator)

        @webpage.setter
        def webpage(self, webpage):
            """Send the URL showing instructor status."""
            self.webpage.send_keys(webpage)
            return self

        @property
        def using(self):
            """Return the instructor's intent field."""
            return self.find_element(*self._using_openstax_locator)

        @using.setter
        def using(self, status):
            """Set the instructor's intent for using OpenStax."""
            Utility.select(self.driver, self._using_openstax_locator, status)
            return self
            # return self.using_openstax(status)

        # Use signup_two's <using> setter
        def using_openstax(self, method):
            """Select the current using state."""
            from utils.accounts import Accounts
            _adopted_locator = (
                By.CSS_SELECTOR,
                '#profile_using_openstax_confirmed_adoption_won')
            _not_using_locator = (
                By.CSS_SELECTOR,
                '#profile_using_openstax_not_using')
            if method == Accounts.ADOPTED:
                option = self.find_element(*_adopted_locator)
            elif method == Accounts.NOT_USING:
                option = self.find_element(*_not_using_locator)
            Utility.click_option(self.driver, element=option)
            return self.page

        @property
        def subjects(self):
            """Return a list of book subjects."""
            return [self.Subject(self, el) for
                    el in self.find_elements(*self._subject_option_locator)]

        def select_subjects(self, subject_list):
            """Mark each interested subject."""
            for subject in self.subjects:
                if subject.title in subject_list:
                    subject.select()
            return self

        class Subject(Region):
            """Book subject."""

            _book_title_locator = (By.CSS_SELECTOR, 'label')
            _checkbox_locator = (By.CSS_SELECTOR, '[type=checkbox]')

            @property
            def title(self):
                """Get the book title."""
                return self.find_element(*self._book_title_locator).text

            def select(self):
                """Select a book."""
                box = self.find_element(*self._checkbox_locator)
                Utility.click_option(self.driver, element=box)
                return self

    class InstructorNotice(Region):
        """Complete the instructor signup."""

        _get_email_confirmation_locator = (By.CSS_SELECTOR, '[type=checkbox]')

        def get_confirmation_email(self):
            """Get an e-mail confirmation when instructor access approved."""
            sleep(0.5)
            confirm = self.find_element(*self._get_email_confirmation_locator)
            Utility.click_option(self.driver, element=confirm)
            return self
