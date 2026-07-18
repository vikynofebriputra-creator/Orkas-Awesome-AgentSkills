import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))
SPEC = importlib.util.spec_from_file_location('social_data_fetch', SCRIPTS_DIR / 'fetch.py')
fetch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch)
import social_fetch_core


class Response:
    status_code = 200

    @staticmethod
    def json():
        return {'data': {'items': [{'id': '1'}, {'id': '2'}]}}


class FetchCliTests(unittest.TestCase):
    def test_runtime_error_includes_platform(self):
        stderr = io.StringIO()

        with patch.dict(fetch.FETCHERS, {'twitter': lambda _config: (_ for _ in ()).throw(RuntimeError('offline'))}):
            with contextlib.redirect_stderr(stderr):
                exit_code = fetch.run_cli(['twitter', 'xquik'])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stderr.getvalue()),
            {'ok': False, 'error': 'RuntimeError: offline', 'platform': 'twitter'},
        )

    def test_empty_keywords_use_json_error_contract(self):
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = fetch.run_cli(['reddit', ' , '])

        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stderr.getvalue()),
            {'ok': False, 'error': 'ValueError: no keywords supplied', 'platform': 'reddit'},
        )


class XquikRequestTests(unittest.TestCase):
    def test_request_passes_count_to_api(self):
        with patch.dict(os.environ, {'XQUIK_API_KEY': 'test-key'}):
            with patch.object(social_fetch_core.requests, 'get', return_value=Response()) as request:
                items = social_fetch_core._fetch_xquik_tweets('agents', 2)

        self.assertEqual(items, [{'id': '1'}, {'id': '2'}])
        request.assert_called_once_with(
            social_fetch_core.XQUIK_SEARCH_URL,
            params={'q': 'agents', 'limit': 2},
            headers={'x-api-key': 'test-key'},
            timeout=30,
        )


if __name__ == '__main__':
    unittest.main()
