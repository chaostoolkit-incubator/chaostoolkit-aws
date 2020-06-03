#
import boto3
import os
import shutil
import placebo
import unittest

from datetime import datetime, timedelta, tzinfo
from botocore.response import StreamingBody
from io import BytesIO
from six import StringIO

###########################################################################
# BEGIN PLACEBO MONKEY PATCH
#
# Placebo is effectively abandoned upstream, since mitch went back to work at
# AWS, irony...
# These monkeypatch patches represent fixes on trunk of that repo that have
# not been released into an extant version, we carry them here. We can drop
# this when this issue is resolved
#
# https://github.com/garnaat/placebo/issues/63
#
# License - Apache 2.0
# Copyright (c) 2015 Mitch Garnaat


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


utc = UTC()


def deserialize(obj):
    """Convert JSON dicts back into objects."""
    # Be careful of shallow copy here
    target = dict(obj)
    class_name = None
    if "__class__" in target:
        class_name = target.pop("__class__")
    if "__module__" in obj:
        obj.pop("__module__")
    # Use getattr(module, class_name) for custom types if needed
    if class_name == "datetime":
        return datetime(tzinfo=utc, **target)
    if class_name == "StreamingBody":
        return BytesIO(target["body"].encode('utf-8'))
    # Return unrecognized structures as-is
    return obj


def serialize(obj):
    """Convert objects into JSON structures."""
    # Record class and module information for deserialization
    result = {"__class__": obj.__class__.__name__}
    try:
        result["__module__"] = obj.__module__
    except AttributeError:
        pass
    # Convert objects to dictionary representation based on type
    if isinstance(obj, datetime):
        result["year"] = obj.year
        result["month"] = obj.month
        result["day"] = obj.day
        result["hour"] = obj.hour
        result["minute"] = obj.minute
        result["second"] = obj.second
        result["microsecond"] = obj.microsecond
        return result
    if isinstance(obj, StreamingBody):
        body_bytes = obj.read()
        result["body"] = body_bytes.decode('utf-8')
        obj._raw_stream = BytesIO(body_bytes)
        obj._amount_read = 0
        return result
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    # Raise a TypeError if the object isn't recognized
    raise TypeError("Type not serializable: {0:s}".format(str(type(obj))))

placebo.serializer.serialize = serialize
placebo.serializer.deserialize = deserialize

# END PLACEBO MONKEY
##########################################################################


class Pharmacy(unittest.TestCase):
    placebo_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test_data")
    recording = False

    def default_session(self):
        if os.environ.get('AWS_PROFILE'):
            boto3.setup_default_session(
                profile_name=os.environ.get('AWS_PROFILE'),
                region_name=os.environ.get('AWS_DEFAULT_REGION'))
        else:
            boto3.setup_default_session(
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=os.environ.get('AWS_DEFAULT_REGION'))
        session = boto3.DEFAULT_SESSION
        return session

    def cleanUp(self):
        pass

    def record_data(self, test_case):
        self.recording = True
        test_dir = os.path.join(self.placebo_dir, test_case)
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        os.makedirs(test_dir)

        session = boto3.Session()
        pill = placebo.attach(session, data_path=test_dir, debug=True)
        pill.record()
        self.addCleanup(self.cleanUp)
        return session

    def replay_data(self, test_case):
        test_dir = os.path.join(self.placebo_dir, test_case)
        if not os.path.exists(test_dir):
            raise RuntimeError('Invalid test directory: %s' % test_dir)

        session = boto3.Session()
        pill = placebo.attach(session, data_path=test_dir)
        pill.playback()
        self.addCleanup(self.cleanUp)
        return session
