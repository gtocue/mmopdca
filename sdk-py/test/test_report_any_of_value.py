# coding: utf-8

"""
mmopdca API

Command-DSL-driven forecasting micro-service API only

The version of the OpenAPI document: 0.4.0
Contact: gtocue510@gmail.com
Generated by OpenAPI Generator (https://openapi-generator.tech)

Do not edit the class manually.
"""  # noqa: E501


import unittest

from mmopdca_sdk.models.report_any_of_value import ReportAnyOfValue


class TestReportAnyOfValue(unittest.TestCase):
    """ReportAnyOfValue unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> ReportAnyOfValue:
        """Test ReportAnyOfValue
        include_optional is a boolean, when False only required
        params are included, when True both required and
        optional params are included"""
        # uncomment below to create an instance of `ReportAnyOfValue`
        """
        model = ReportAnyOfValue()
        if include_optional:
            return ReportAnyOfValue(
            )
        else:
            return ReportAnyOfValue(
        )
        """

    def testReportAnyOfValue(self):
        """Test ReportAnyOfValue"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == "__main__":
    unittest.main()
