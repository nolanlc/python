import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

import getRandomUsers


class TestGetRandomUsersMain(unittest.TestCase):
    def run_main_with_status(self, status_code):
        fake_response = mock.Mock(status_code=status_code)
        buf = io.StringIO()
        with mock.patch("getRandomUsers.requests.get", return_value=fake_response) as mock_get, \
                redirect_stdout(buf):
            getRandomUsers.main()
        mock_get.assert_called_once_with("https://randomuser.me/api/")
        return buf.getvalue()

    def test_status_200_prints_ok(self):
        self.assertEqual(self.run_main_with_status(200), "Request Status OK!\n")

    def test_non_200_prints_error_code(self):
        self.assertEqual(self.run_main_with_status(500), "Error Code 500\n")

    def test_404_prints_error_code(self):
        self.assertEqual(self.run_main_with_status(404), "Error Code 404\n")


if __name__ == "__main__":
    unittest.main()
