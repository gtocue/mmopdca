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

from mmopdca_sdk.api.act_api import ActApi


class TestActApi(unittest.TestCase):
    """ActApi unit test stubs"""

    def setUp(self) -> None:
        self.api = ActApi()

    def tearDown(self) -> None:
        pass

    def test_create_act_act_check_id_post(self) -> None:
        """Test case for create_act_act_check_id_post

        Run Act (decide next action)
        """
        pass

    def test_get_act_act_act_id_get(self) -> None:
        """Test case for get_act_act_act_id_get

        Get ActDecision
        """
        pass

    def test_list_act_act_get(self) -> None:
        """Test case for list_act_act_get

        List ActDecision
        """
        pass


if __name__ == "__main__":
    unittest.main()
