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

from mmopdca_sdk.api.do_api import DoApi


class TestDoApi(unittest.TestCase):
    """DoApi unit test stubs"""

    def setUp(self) -> None:
        self.api = DoApi()

    def tearDown(self) -> None:
        pass

    def test_enqueue_do_do_plan_id_post(self) -> None:
        """Test case for enqueue_do_do_plan_id_post

        Enqueue Do job (Celery)
        """
        pass

    def test_get_do_do_do_id_get(self) -> None:
        """Test case for get_do_do_do_id_get

        Get Do record
        """
        pass

    def test_get_do_status_do_status_task_id_get(self) -> None:
        """Test case for get_do_status_do_status_task_id_get

        Raw Celery task state
        """
        pass

    def test_list_do_do_get(self) -> None:
        """Test case for list_do_do_get

        List Do records
        """
        pass


if __name__ == "__main__":
    unittest.main()
