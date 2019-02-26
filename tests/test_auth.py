# -*- coding: utf-8 -*-
import json
from unittest.mock import MagicMock, patch, ANY
from urllib.parse import urlparse, parse_qs

import requests_mock

from chaosaws import aws_client, get_credentials, signed_api_call


CONFIGURATION = {
    "aws_region": "us-east-1",
    "aws_host": "localhost",
    "aws_endpoint_scheme": "http",
}

CONFIG_WITH_PROFILE = {
    "aws_profile_name": "myprofile"
}

CONFIG_WITH_ARN = {
    "aws_assume_role_arn": "myarn"
}

CONFIG_WITH_ARN_AND_PROFILE = {
    "aws_profile_name": "myprofile",
    "aws_assume_role_arn": "myarn"
}

SECRETS = {
    "aws_access_key_id": "mykey",
    "aws_secret_access_key": "mysecret",
    "aws_session_token": "mytoken",
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


@patch('chaosaws.boto3', autospec=True)
def test_create_client_from_cred_keys(boto3: object):
    boto3.DEFAULT_SESSION = None
    creds = get_credentials(SECRETS)

    aws_client('ecs', configuration=CONFIGURATION, secrets=SECRETS)
    boto3.client.assert_called_with(
        'ecs', region_name="us-east-1", **creds)

    aws_client('ecs', configuration=CONFIGURATION, secrets=SECRETS)
    boto3.setup_default_session.assert_called_with(
        profile_name=None, region_name="us-east-1", **creds)
    boto3.client.assert_called_with(
        'ecs', region_name="us-east-1", **creds)


@patch('chaosaws.boto3', autospec=True)
def test_create_client_from_profile_name(boto3: object):
    boto3.DEFAULT_SESSION = None
    creds = get_credentials(dict())

    aws_client(
        'ecs', configuration=CONFIG_WITH_PROFILE)
    boto3.client.assert_called_with(
        'ecs', region_name="us-east-1", **creds)

    aws_client(
        'ecs', configuration=CONFIG_WITH_PROFILE)
    boto3.setup_default_session.assert_called_with(
        profile_name="myprofile", region_name="us-east-1", **creds)
    boto3.client.assert_called_with(
        'ecs', region_name="us-east-1", **creds)


@patch('chaosaws.boto3', autospec=True)
def test_create_client_with_aws_role_arn(boto3: object):
    boto3.DEFAULT_SESSION = None
    creds = get_credentials(dict())
    finalArgs = {}

    aws_client(
        'ecs', configuration=CONFIG_WITH_ARN)
    boto3.client.assert_any_call(
        'sts', region_name="us-east-1", **creds)
    boto3.client.assert_called_with(
            'ecs',
            region_name="us-east-1",
            aws_access_key_id=ANY,
            aws_secret_access_key=ANY,
            aws_session_token=ANY)

    aws_client(
        'ecs', configuration=CONFIG_WITH_ARN)
    boto3.client.assert_any_call(
        'sts', region_name="us-east-1", **creds)
    boto3.setup_default_session.assert_called_with(
            profile_name=None, region_name="us-east-1", **creds)
    boto3.client.assert_called_with(
            'ecs',
            region_name="us-east-1",
            aws_access_key_id=ANY,
            aws_secret_access_key=ANY,
            aws_session_token=ANY)


@patch('chaosaws.boto3', autospec=True)
def test_create_client_with_aws_role_arn_and_profile(boto3: object):
    boto3.DEFAULT_SESSION = None
    creds = get_credentials(dict())
    finalArgs = {}

    aws_client(
        'ecs', configuration=CONFIG_WITH_ARN_AND_PROFILE)
    boto3.client.assert_any_call(
        'sts', region_name="us-east-1", **creds)
    boto3.client.assert_called_with(
            'ecs',
            region_name="us-east-1",
            aws_access_key_id=ANY,
            aws_secret_access_key=ANY,
            aws_session_token=ANY)

    aws_client(
        'ecs', configuration=CONFIG_WITH_ARN_AND_PROFILE)
    boto3.client.assert_any_call(
        'sts', region_name="us-east-1", **creds)
    boto3.setup_default_session.assert_called_with(
            profile_name="myprofile", region_name="us-east-1", **creds)
    boto3.client.assert_called_with(
            'ecs',
            region_name="us-east-1",
            aws_access_key_id=ANY,
            aws_secret_access_key=ANY,
            aws_session_token=ANY)
