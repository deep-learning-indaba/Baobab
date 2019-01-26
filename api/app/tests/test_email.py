import unittest
from app.utils.emailer import send_mail
from app import LOGGER

class TestMailer(unittest.TestCase):
    def test_send_email(self):
        try:
            LOGGER.info("Testing mailer")
            #send_mail(recipient='nischal.hp@gmail.com', subject='TestSMTPEmail', body_text='Hello world from Amazon SES')
            return True
        except Exception:
            return False

if __name__ == '__main__':
    unittest.main()
