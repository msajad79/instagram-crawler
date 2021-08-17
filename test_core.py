import unittest

from core import Account
from secret_data import TRUE_PROFILES


class TestCoreLogin(unittest.TestCase):
    def setUp(self) -> None:
        self.FALSE_PROFILES = [
            {
                'username': 'usernameinvalid',
                'password': 'passinvalid',
            }
        ]

    
    def test_login_false(self):
        for profile in self.FALSE_PROFILES:
            account = Account(username=profile['username'], password=profile['password'])
            ans_login = account.login()
            self.assertFalse(ans_login['authenticated'])
            self.assertEqual(ans_login['status'], 'ok')

    def test_login_true(self):
        for profile in TRUE_PROFILES:
            account = Account(username=profile['username'], password=profile['password'])
            ans_login = account.login()
            self.assertTrue(ans_login['user'])
            self.assertTrue(ans_login['authenticated'])
            self.assertEqual(ans_login['status'], 'ok')
            self.assertEqual(account.userId, profile['userId'])
    
class TestCoreLogout(unittest.TestCase):
    def setUp(self) -> None:
        self.acconts = list()
        for profile in TRUE_PROFILES:
            account = Account(username=profile['username'], password=profile['password'])
            csrf_token = account.get_csrf_token()
            ans_login = account.login(csrf=csrf_token)
            self.acconts.append(account)

    def test_logout(self):
        for account in self.acconts:
            account.logout()




if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestCoreLogout("test_logout"))
    runner = unittest.TextTestRunner()
    runner.run(suite)



