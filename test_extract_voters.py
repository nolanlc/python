import io
import json
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest import mock

import extract_voters


class TestBuildFullName(unittest.TestCase):
    def test_skips_none_component(self):
        self.assertEqual(
            extract_voters.build_full_name("Mr", "John", None, "Doe", "Jr"),
            "Mr John Doe Jr",
        )

    def test_all_components(self):
        self.assertEqual(
            extract_voters.build_full_name("Dr", "Jane", "Q", "Public", "III"),
            "Dr Jane Q Public III",
        )

    def test_skips_empty_strings(self):
        self.assertEqual(
            extract_voters.build_full_name("", "John", "", "Doe", ""),
            "John Doe",
        )

    def test_strips_whitespace(self):
        self.assertEqual(
            extract_voters.build_full_name(None, " John ", None, " Doe", None),
            "John Doe",
        )

    def test_all_empty(self):
        self.assertEqual(extract_voters.build_full_name(None, None, "", None, None), "")


class TestBuildAddress(unittest.TestCase):
    def test_full_address_with_int_zip(self):
        self.assertEqual(
            extract_voters.build_address("123", "123 Main St", "Springfield", "IL", 62701),
            "123 Main St, Springfield, IL, 62701",
        )

    def test_string_zip(self):
        self.assertEqual(
            extract_voters.build_address("1", "1 Elm St", "Austin", "TX", "78701"),
            "1 Elm St, Austin, TX, 78701",
        )

    def test_skips_empty_parts(self):
        self.assertEqual(
            extract_voters.build_address("5", "5 Oak Ave", "", "CA", None),
            "5 Oak Ave, CA",
        )

    def test_house_number_not_included(self):
        self.assertEqual(
            extract_voters.build_address("999", "10 Pine Rd", "Reno", "NV", 89501),
            "10 Pine Rd, Reno, NV, 89501",
        )


def fake_urlopen_response(payload):
    response = mock.MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    response.__enter__.return_value = response
    return response


class TestGetAddressType(unittest.TestCase):
    def assert_type_for_metadata(self, metadata, expected):
        payload = {"result": {"metadata": metadata}}
        with mock.patch(
            "extract_voters.urllib.request.urlopen",
            return_value=fake_urlopen_response(payload),
        ) as mock_urlopen:
            result = extract_voters.get_address_type("123 Main St, Springfield, IL, 62701")
        self.assertEqual(result, expected)
        mock_urlopen.assert_called_once()

    def test_residential(self):
        self.assert_type_for_metadata({"residential": True}, "Residential")

    def test_business(self):
        self.assert_type_for_metadata({"business": True}, "Business")

    def test_po_box(self):
        self.assert_type_for_metadata({"poBox": True}, "PO Box")

    def test_unknown_when_no_flags(self):
        self.assert_type_for_metadata({}, "Unknown")

    def test_unknown_when_no_result(self):
        with mock.patch(
            "extract_voters.urllib.request.urlopen",
            return_value=fake_urlopen_response({}),
        ):
            self.assertEqual(extract_voters.get_address_type("anywhere"), "Unknown")

    def test_residential_takes_precedence(self):
        self.assert_type_for_metadata({"residential": True, "business": True}, "Residential")

    def test_request_payload(self):
        with mock.patch(
            "extract_voters.urllib.request.urlopen",
            return_value=fake_urlopen_response({}),
        ) as mock_urlopen:
            extract_voters.get_address_type("1 Elm St")
        req = mock_urlopen.call_args.args[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.full_url, extract_voters.VALIDATE_URL)
        self.assertEqual(req.get_header("Content-type"), "application/json")
        self.assertEqual(json.loads(req.data), {"address": {"addressLines": ["1 Elm St"]}})

    def test_http_error(self):
        error = urllib.error.HTTPError(
            extract_voters.VALIDATE_URL, 403, "Forbidden", hdrs=None, fp=None
        )
        with mock.patch("extract_voters.urllib.request.urlopen", side_effect=error):
            self.assertEqual(extract_voters.get_address_type("1 Elm St"), "API error 403")


class TestGetRecordLimit(unittest.TestCase):
    def call_with_inputs(self, inputs):
        buf = io.StringIO()
        with mock.patch("builtins.input", side_effect=inputs) as mock_input, redirect_stdout(buf):
            result = extract_voters.get_record_limit()
        return result, mock_input.call_count, buf.getvalue()

    def test_valid_number(self):
        result, calls, _ = self.call_with_inputs(["5"])
        self.assertEqual(result, 5)
        self.assertEqual(calls, 1)

    def test_number_with_whitespace(self):
        result, _, _ = self.call_with_inputs(["  12  "])
        self.assertEqual(result, 12)

    def test_all_returns_none(self):
        result, _, _ = self.call_with_inputs(["ALL"])
        self.assertIsNone(result)

    def test_all_case_insensitive(self):
        result, _, _ = self.call_with_inputs(["all"])
        self.assertIsNone(result)

    def test_retries_on_invalid_input(self):
        result, calls, output = self.call_with_inputs(["abc", "0", "-3", "", "7"])
        self.assertEqual(result, 7)
        self.assertEqual(calls, 5)
        self.assertEqual(output.count("Please enter a positive number or ALL."), 4)


class TestGetOutputFilter(unittest.TestCase):
    def call_with_inputs(self, inputs):
        buf = io.StringIO()
        with mock.patch("builtins.input", side_effect=inputs) as mock_input, redirect_stdout(buf):
            result = extract_voters.get_output_filter()
        return result, mock_input.call_count, buf.getvalue()

    def test_option_1(self):
        result, calls, output = self.call_with_inputs(["1"])
        self.assertEqual(result, "1")
        self.assertEqual(calls, 1)
        self.assertIn("Output options:", output)

    def test_option_2_with_whitespace(self):
        result, _, _ = self.call_with_inputs([" 2 "])
        self.assertEqual(result, "2")

    def test_retries_on_invalid_input(self):
        result, calls, output = self.call_with_inputs(["3", "ALL", "", "2"])
        self.assertEqual(result, "2")
        self.assertEqual(calls, 4)
        self.assertEqual(output.count("Please enter 1 or 2."), 3)


if __name__ == "__main__":
    unittest.main()
