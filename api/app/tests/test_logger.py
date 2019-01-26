import unittest
from api.app.utils.logger import Logger
import sys
import io


class TestLogger(unittest.TestCase):
    def test_normal_logger(self):
        out = io.StringIO()
        LOGGER = Logger().get_logger()
        test_string = 'Hello World'
        LOGGER.info(test_string)
        output = out.getvalue().strip()
        if test_string in output:
            return True
        else:
            return False

    def test_logger_with_exception(self):
        LOGGER = Logger().get_logger()
        try:
            out = io.StringIO()
            a = 100
            b = 0
            c = a/b
        except Exception as e:
            LOGGER.error("Exception has occured", exc_info=True)
            output = out.getvalue().strip()
            if "ZeroDivisionError" in output:
                return True
            else:
                return False

if __name__ == "__main__":
    unittest.main()
