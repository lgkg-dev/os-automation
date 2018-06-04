"""Test the Accounts signup process."""
import os

from pytest_testrail.plugin import pytestrail

from pages.accounts.signup import Signup
from pages.utils.email import GuerrillaMail
from pages.utils.utilities import Utility


@pytestrail.case('C195549')
def test_student_account_signup(base_url, selenium):
    """Test student user signup."""
    page = GuerrillaMail(selenium, base_url).open()
    email = page.header.email
    page = Signup(selenium, base_url).open()
    page.account_signup(
        email=email,
        password=os.getenv('STUDENT_PASSWORD'),
        _type=Signup.STUDENT,
        provider='guerrilla',
        kwargs={
            'name': Utility.random_name(),
            'school': 'OpenStax Automation',
            'news': False,
        }
    )
    assert('org/profile' in selenium.current_url), \
        'Not logged in as a new student'


@pytestrail.case('C205362')
def test_instructor_account_signup(base_url, selenium):
    """Test non-student user signup."""
    page = GuerrillaMail(selenium, base_url).open()
    email = page.header.email
    page = Signup(selenium, base_url).open()
    subjects = subject_list(Utility.random(1, 5))
    page.account_signup(
        email=email,
        password=os.getenv('TEACHER_PASSWORD'),
        _type=Signup.INSTRUCTOR,
        provider='guerrilla',
        kwargs={
            'name': Utility.random_name(),
            'news': False,
            'phone': Utility.random_phone(),
            'school': 'OpenStax Automation',
            'students': 40,
            'subjects': subjects,
            'use': Signup.INTEREST,
            'webpage': 'http://openstax.org'
        }
    )
    assert('profile' in selenium.current_url), \
        'Not logged in as a new instructor'


@pytestrail.case('C195550')
def test_non_student_account_signup(base_url, selenium):
    """Test non-student user signup."""
    page = GuerrillaMail(selenium, base_url).open()
    email = page.header.email
    page = Signup(selenium, base_url).open()
    # collect the options besides the initial value, student and teacher
    options = [
        ('administrator', Signup.ADMINISTRATOR),
        ('librarian', Signup.LIBRARIAN),
        ('designer', Signup.DESIGNER),
        ('other', Signup.OTHER),
    ]
    # select the type randomly to test each type over time
    choice = Utility.random(0, len(options) - 1)
    (account_type, account_title) = options[choice]
    subjects = subject_list(Utility.random(1, 5))
    page.account_signup(
        email=email,
        password=os.getenv('TEACHER_PASSWORD'),
        _type=account_title,
        provider='guerrilla',
        kwargs={
            'name': Utility.random_name(),
            'news': False,
            'phone': Utility.random_phone(),
            'school': 'OpenStax Automation',
            'students': 40,
            'subjects': subjects,
            'use': Signup.INTEREST,
            'webpage': 'http://openstax.org'
        }
    )
    assert('profile' in selenium.current_url), \
        'Not logged in as a new {0}'.format(account_type)


def subject_list(size=1):
    """Return a list of subjects for an elevated signup."""
    subjects = len(Signup.SUBJECTS)
    if size > subjects:
        size = subjects
    book = ''
    group = []
    while len(group) < size:
        book = (Signup.SUBJECTS[Utility.random(0, subjects - 1)])[1]
        if book not in group:
            group.append(book)
    return group
