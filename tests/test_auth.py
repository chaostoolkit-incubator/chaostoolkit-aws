# -*- coding: utf-8 -*-
import json
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse, parse_qs

import requests_mock

from chaosaws import signed_api_call


CONFIGURATION = {
    "aws_region": "us-east-1",
    "aws_host": "localhost",
    "aws_endpoint_scheme": "http",
}

SECRETS = {
    "aws_access_key_id": "mykey",
    "aws_secret_access_key": "mysecret",
    "aws_session_token": "mytoken"
}

ENDPOINT = "http://eks.us-east-1.localhost"


def test_signed_api_call_with_params():
    with requests_mock.Mocker() as m:
        url = '{}/some/path'.format(ENDPOINT)
        m.get(url, complete_qs=False, text="someresponse")

        r = signed_api_call(
            'eks',
            path='/some/path',
            configuration=CONFIGURATION,
            secrets=SECRETS,
            params={
                "Action": "Terminate",
                "NodeId.1": "12345"
            }
        )

        assert 'Authorization' in r.request.headers
        assert r.text == "someresponse"

        p = urlparse(r.request.url)
        assert p.query is not None

        q = parse_qs(p.query)
        
        assert "Action" in q
        assert q["Action"] == ["Terminate"]

        assert "NodeId.1" in q
        assert q["NodeId.1"] == ["12345"]


def test_signed_api_call_with_body():
    with requests_mock.Mocker() as m:
        url = '{}/some/path'.format(ENDPOINT)
        m.post(url, complete_qs=False, text="someresponse")

        r = signed_api_call(
            'eks',
            path='/some/path',
            configuration=CONFIGURATION,
            secrets=SECRETS,
            method='POST',
            params={
                "Action": "Terminate",
                "NodeId.1": "12345"
            }
        )

        assert 'Authorization' in r.request.headers
        assert r.text == "someresponse"

        body = json.loads(r.request.body.decode('utf-8'))
        
        assert "Action" in body
        assert body["Action"] == "Terminate"

        assert "NodeId.1" in body
        assert body["NodeId.1"] == "12345"
