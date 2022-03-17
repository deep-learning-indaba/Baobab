import io
import sys
import unittest

from app.utils.logger import Logger


class TestLogger(unittest.TestCase):
    def test_normal_logger(self):
        out = io.StringIO()
        LOGGER = Logger().get_logger()
        test_string = "Hello World"
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
            a / b
        except Exception:
            LOGGER.error("Exception has occured", exc_info=True)
            output = out.getvalue().strip()
            if "ZeroDivisionError" in output:
                return True
            else:
                return False


if __name__ == "__main__":
    unittest.main()
