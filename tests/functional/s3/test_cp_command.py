#!/usr/bin/env python
# Copyright 2013 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import mock
import os

from awscli.testutils import BaseAWSCommandParamsTest
from awscli.testutils import capture_input, set_invalid_utime
from awscli.testutils import skip_if_windows, skip_if_macos
from awscli.compat import six
from tests.functional.s3 import BaseS3TransferCommandTest


class BufferedBytesIO(six.BytesIO):
    @property
    def buffer(self):
        return self


class BaseCPCommandTest(BaseS3TransferCommandTest):
    prefix = 's3 cp '


class TestCPCommand(BaseCPCommandTest):
    def test_operations_used_in_upload(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = '%s %s s3://bucket/key.txt' % (self.prefix, full_path)
        self.parsed_responses = [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        # The only operation we should have called is PutObject.
        self.assertEqual(len(self.operations_called), 1, self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')

    def test_key_name_added_when_only_bucket_provided(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = '%s %s s3://bucket/' % (self.prefix, full_path)
        self.parsed_responses = [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        # The only operation we should have called is PutObject.
        self.assertEqual(len(self.operations_called), 1, self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        self.assertEqual(self.operations_called[0][1]['Key'], 'foo.txt')
        self.assertEqual(self.operations_called[0][1]['Bucket'], 'bucket')

    def test_trailing_slash_appended(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        # Here we're saying s3://bucket instead of s3://bucket/
        # This should still work the same as if we added the trailing slash.
        cmdline = '%s %s s3://bucket' % (self.prefix, full_path)
        self.parsed_responses = [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        # The only operation we should have called is PutObject.
        self.assertEqual(len(self.operations_called), 1, self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        self.assertEqual(self.operations_called[0][1]['Key'], 'foo.txt')
        self.assertEqual(self.operations_called[0][1]['Bucket'], 'bucket')

    def test_upload_grants(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = ('%s %s s3://bucket/key.txt --grants read=id=foo '
                   'full=id=bar readacl=id=biz writeacl=id=baz' %
                   (self.prefix, full_path))
        self.parsed_responses = \
            [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        # The only operation we should have called is PutObject.
        self.assertEqual(len(self.operations_called), 1,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        self.assertDictEqual(
            self.operations_called[0][1],
            {'Key': u'key.txt', 'Bucket': u'bucket', 'GrantRead': u'id=foo',
             'GrantFullControl': u'id=bar', 'GrantReadACP': u'id=biz',
             'GrantWriteACP': u'id=baz', 'ContentType': u'text/plain',
             'Body': mock.ANY}
        )

    def test_upload_expires(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = ('%s %s s3://bucket/key.txt --expires 90' %
                   (self.prefix, full_path))
        self.parsed_responses = \
            [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        # The only operation we should have called is PutObject.
        self.assertEqual(len(self.operations_called), 1,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        self.assertEqual(self.operations_called[0][1]['Key'], 'key.txt')
        self.assertEqual(self.operations_called[0][1]['Bucket'], 'bucket')
        self.assertEqual(self.operations_called[0][1]['Expires'], '90')

    def test_upload_standard_ia(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = ('%s %s s3://bucket/key.txt --storage-class STANDARD_IA' %
                   (self.prefix, full_path))
        self.parsed_responses = \
            [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        args = self.operations_called[0][1]
        self.assertEqual(args['Key'], 'key.txt')
        self.assertEqual(args['Bucket'], 'bucket')
        self.assertEqual(args['StorageClass'], 'STANDARD_IA')

    def test_upload_onezone_ia(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = ('%s %s s3://bucket/key.txt --storage-class ONEZONE_IA' %
                   (self.prefix, full_path))
        self.parsed_responses = \
            [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        args = self.operations_called[0][1]
        self.assertEqual(args['Key'], 'key.txt')
        self.assertEqual(args['Bucket'], 'bucket')
        self.assertEqual(args['StorageClass'], 'ONEZONE_IA')

    def test_upload_intelligent_tiering(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = ('%s %s s3://bucket/key.txt --storage-class INTELLIGENT_TIERING' %
                   (self.prefix, full_path))
        self.parsed_responses = \
            [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        args = self.operations_called[0][1]
        self.assertEqual(args['Key'], 'key.txt')
        self.assertEqual(args['Bucket'], 'bucket')
        self.assertEqual(args['StorageClass'], 'INTELLIGENT_TIERING')

    def test_upload_glacier(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = ('%s %s s3://bucket/key.txt --storage-class GLACIER' %
                   (self.prefix, full_path))
        self.parsed_responses = \
            [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        args = self.operations_called[0][1]
        self.assertEqual(args['Key'], 'key.txt')
        self.assertEqual(args['Bucket'], 'bucket')
        self.assertEqual(args['StorageClass'], 'GLACIER')

    def test_upload_deep_archive(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = ('%s %s s3://bucket/key.txt --storage-class DEEP_ARCHIVE' %
                   (self.prefix, full_path))
        self.parsed_responses = \
            [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        args = self.operations_called[0][1]
        self.assertEqual(args['Key'], 'key.txt')
        self.assertEqual(args['Bucket'], 'bucket')
        self.assertEqual(args['StorageClass'], 'DEEP_ARCHIVE')

    def test_operations_used_in_download_file(self):
        self.parsed_responses = [
            {"ContentLength": "100", "LastModified": "00:00:00Z"},
            {'ETag': '"foo-1"', 'Body': six.BytesIO(b'foo')},
        ]
        cmdline = '%s s3://bucket/key.txt %s' % (self.prefix,
                                                 self.files.rootdir)
        self.run_cmd(cmdline, expected_rc=0)
        # The only operations we should have called are HeadObject/GetObject.
        self.assertEqual(len(self.operations_called), 2, self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'HeadObject')
        self.assertEqual(self.operations_called[1][0].name, 'GetObject')

    def test_operations_used_in_recursive_download(self):
        self.parsed_responses = [
            {'ETag': '"foo-1"', 'Contents': [], 'CommonPrefixes': []},
        ]
        cmdline = '%s s3://bucket/key.txt %s --recursive' % (
            self.prefix, self.files.rootdir)
        self.run_cmd(cmdline, expected_rc=0)
        # We called ListObjectsV2 but had no objects to download, so
        # we only have a single ListObjectsV2 operation being called.
        self.assertEqual(len(self.operations_called), 1, self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'ListObjectsV2')

    def test_website_redirect_ignore_paramfile(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = '%s %s s3://bucket/key.txt --website-redirect %s' % \
            (self.prefix, full_path, 'http://someserver')
        self.parsed_responses = [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        # Make sure that the specified web address is used as opposed to the
        # contents of the web address.
        self.assertEqual(
            self.operations_called[0][1]['WebsiteRedirectLocation'],
            'http://someserver'
        )

    def test_metadata_copy(self):
        self.parsed_responses = [
            {"ContentLength": "100", "LastModified": "00:00:00Z"},
            {'ETag': '"foo-1"'},
        ]
        cmdline = ('%s s3://bucket/key.txt s3://bucket/key2.txt'
                   ' --metadata KeyName=Value' % self.prefix)
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 2,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'HeadObject')
        self.assertEqual(self.operations_called[1][0].name, 'CopyObject')
        self.assertEqual(self.operations_called[1][1]['Metadata'],
                         {'KeyName': 'Value'})

    def test_metadata_copy_with_put_object(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        self.parsed_responses = [
            {"ContentLength": "100", "LastModified": "00:00:00Z"},
            {'ETag': '"foo-1"'},
        ]
        cmdline = ('%s %s s3://bucket/key2.txt'
                   ' --metadata KeyName=Value' % (self.prefix, full_path))
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        self.assertEqual(self.operations_called[0][1]['Metadata'],
                         {'KeyName': 'Value'})

    def test_metadata_copy_with_multipart_upload(self):
        full_path = self.files.create_file('foo.txt', 'a' * 10 * (1024 ** 2))
        self.parsed_responses = [
            {'UploadId': 'foo'},
            {'ETag': '"foo-1"'},
            {'ETag': '"foo-2"'},
            {}
        ]
        cmdline = ('%s %s s3://bucket/key2.txt'
                   ' --metadata KeyName=Value' % (self.prefix, full_path))
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 4,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name,
                         'CreateMultipartUpload')
        self.assertEqual(self.operations_called[0][1]['Metadata'],
                         {'KeyName': 'Value'})

    def test_metadata_directive_copy(self):
        self.parsed_responses = [
            {"ContentLength": "100", "LastModified": "00:00:00Z"},
            {'ETag': '"foo-1"'},
        ]
        cmdline = ('%s s3://bucket/key.txt s3://bucket/key2.txt'
                   ' --metadata-directive REPLACE' % self.prefix)
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 2,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'HeadObject')
        self.assertEqual(self.operations_called[1][0].name, 'CopyObject')
        self.assertEqual(self.operations_called[1][1]['MetadataDirective'],
                         'REPLACE')

    def test_no_metadata_directive_for_non_copy(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = '%s %s s3://bucket --metadata-directive REPLACE' % \
            (self.prefix, full_path)
        self.parsed_responses = \
            [{'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1,
                         self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        self.assertNotIn('MetadataDirective', self.operations_called[0][1])

    def test_cp_succeeds_with_mimetype_errors(self):
        full_path = self.files.create_file('foo.txt', 'mycontent')
        cmdline = '%s %s s3://bucket/key.txt' % (self.prefix, full_path)
        self.parsed_responses = [
            {'ETag': '"c8afdb36c52cf4727836669019e69222"'}]
        with mock.patch('mimetypes.guess_type') as mock_guess_type:
            # This should throw a UnicodeDecodeError.
            mock_guess_type.side_effect = lambda x: b'\xe2'.decode('ascii')
            self.run_cmd(cmdline, expected_rc=0)
        # Because of the decoding error the command should have succeeded
        # just that there was no content type added.
        self.assertNotIn('ContentType', self.last_kwargs)

    def test_cp_fails_with_utime_errors_but_continues(self):
        full_path = self.files.create_file('foo.txt', '')
        cmdline = '%s s3://bucket/key.txt %s' % (self.prefix, full_path)
        self.parsed_responses = [
            {"ContentLength": "100", "LastModified": "00:00:00Z"},
            {'ETag': '"foo-1"', 'Body': six.BytesIO(b'foo')}
        ]
        with mock.patch('os.utime') as mock_utime:
            mock_utime.side_effect = OSError(1, '')
            _, err, _ = self.run_cmd(cmdline, expected_rc=2)
            self.assertIn('attempting to modify the utime', err)

    def test_recursive_glacier_download_with_force_glacier(self):
        self.parsed_responses = [
            {
                'Contents': [
                    {'Key': 'foo/bar.txt', 'ContentLength': '100',
                     'LastModified': '00:00:00Z',
                     'StorageClass': 'GLACIER',
                     'Size': 100},
                ],
                'CommonPrefixes': []
            },
            {'ETag': '"foo-1"', 'Body': six.BytesIO(b'foo')},
        ]
        cmdline = '%s s3://bucket/foo %s --recursive --force-glacier-transfer'\
                  % (self.prefix, self.files.rootdir)
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 2, self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'ListObjectsV2')
        self.assertEqual(self.operations_called[1][0].name, 'GetObject')

    def test_recursive_glacier_download_without_force_glacier(self):
        self.parsed_responses = [
            {
                'Contents': [
                    {'Key': 'foo/bar.txt', 'ContentLength': '100',
                     'LastModified': '00:00:00Z',
                     'StorageClass': 'GLACIER',
                     'Size': 100},
                ],
                'CommonPrefixes': []
            }
        ]
        cmdline = '%s s3://bucket/foo %s --recursive' % (
            self.prefix, self.files.rootdir)
        _, stderr, _ = self.run_cmd(cmdline, expected_rc=2)
        self.assertEqual(len(self.operations_called), 1, self.operations_called)
        self.assertEqual(self.operations_called[0][0].name, 'ListObjectsV2')
        self.assertIn('GLACIER', stderr)

    def test_warns_on_glacier_incompatible_operation(self):
        self.parsed_responses = [
            {'ContentLength': '100', 'LastModified': '00:00:00Z',
             'StorageClass': 'GLACIER'},
        ]
        cmdline = ('%s s3://bucket/key.txt .' % self.prefix)
        _, stderr, _ = self.run_cmd(cmdline, expected_rc=2)
        # There should not have been a download attempted because the
        # operation was skipped because it is glacier incompatible.
        self.assertEqual(len(self.operations_called), 1)
        self.assertEqual(self.operations_called[0][0].name, 'HeadObject')
        self.assertIn('GLACIER', stderr)

    def test_warns_on_glacier_incompatible_operation_for_multipart_file(self):
        self.parsed_responses = [
            {'ContentLength': str(20 * (1024 ** 2)),
             'LastModified': '00:00:00Z',
             'StorageClass': 'GLACIER'},
        ]
        cmdline = ('%s s3://bucket/key.txt .' % self.prefix)
        _, stderr, _ = self.run_cmd(cmdline, expected_rc=2)
        # There should not have been a download attempted because the
        # operation was skipped because it is glacier incompatible.
        self.assertEqual(len(self.operations_called), 1)
        self.assertEqual(self.operations_called[0][0].name, 'HeadObject')
        self.assertIn('GLACIER', stderr)

    def test_turn_off_glacier_warnings(self):
        self.parsed_responses = [
            {'ContentLength': str(20 * (1024 ** 2)),
             'LastModified': '00:00:00Z',
             'StorageClass': 'GLACIER'},
        ]
        cmdline = (
            '%s s3://bucket/key.txt . --ignore-glacier-warnings' % self.prefix)
        _, stderr, _ = self.run_cmd(cmdline, expected_rc=0)
        # There should not have been a download attempted because the
        # operation was skipped because it is glacier incompatible.
        self.assertEqual(len(self.operations_called), 1)
        self.assertEqual(self.operations_called[0][0].name, 'HeadObject')
        self.assertEqual('', stderr)

    def test_cp_with_sse_flag(self):
        full_path = self.files.create_file('foo.txt', 'contents')
        cmdline = (
            '%s %s s3://bucket/key.txt --sse' % (
                self.prefix, full_path))
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        self.assertDictEqual(
            self.operations_called[0][1],
            {'Key': 'key.txt', 'Bucket': 'bucket',
             'ContentType': 'text/plain', 'Body': mock.ANY,
             'ServerSideEncryption': 'AES256'}
        )

    def test_cp_with_sse_c_flag(self):
        full_path = self.files.create_file('foo.txt', 'contents')
        cmdline = (
            '%s %s s3://bucket/key.txt --sse-c --sse-c-key foo' % (
                self.prefix, full_path))
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        self.assertDictEqual(
            self.operations_called[0][1],
            {'Key': 'key.txt', 'Bucket': 'bucket',
             'ContentType': 'text/plain', 'Body': mock.ANY,
             'SSECustomerAlgorithm': 'AES256', 'SSECustomerKey': 'Zm9v',
             'SSECustomerKeyMD5': 'rL0Y20zC+Fzt72VPzMSk2A=='}
        )

    def test_cp_with_sse_c_fileb(self):
        file_path = self.files.create_file('foo.txt', 'contents')
        key_path = self.files.create_file('foo.key', '')
        with open(key_path, 'wb') as f:
            f.write(
                b'K\xc9G\xe1\xf9&\xee\xd1\x03\xf3\xd4\x10\x18o9E\xc2\xaeD'
                b'\x89(\x18\xea\xda\xf6\x81\xc3\xd2\x9d\\\xa8\xe6'
            )
        cmdline = (
            '%s %s s3://bucket/key.txt --sse-c --sse-c-key fileb://%s' % (
                self.prefix, file_path, key_path
            )
        )
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')

        expected_args = {
            'Key': 'key.txt', 'Bucket': 'bucket',
            'ContentType': 'text/plain',
            'Body': mock.ANY,
            'SSECustomerAlgorithm': 'AES256',
            'SSECustomerKey': 'S8lH4fkm7tED89QQGG85RcKuRIkoGOra9oHD0p1cqOY=',
            'SSECustomerKeyMD5': 'mL8/mshNgBObhAC1j5BOLw=='
        }
        self.assertDictEqual(self.operations_called[0][1], expected_args)

    def test_cp_with_sse_c_copy_source_fileb(self):
        self.parsed_responses = [
            {
                "AcceptRanges": "bytes",
                "LastModified": "Tue, 12 Jul 2016 21:26:07 GMT",
                "ContentLength": 4,
                "ETag": '"d3b07384d113edec49eaa6238ad5ff00"',
                "Metadata": {},
                "ContentType": "binary/octet-stream"
            },
            {
                "AcceptRanges": "bytes",
                "Metadata": {},
                "ContentType": "binary/octet-stream",
                "ContentLength": 4,
                "ETag": '"d3b07384d113edec49eaa6238ad5ff00"',
                "LastModified": "Tue, 12 Jul 2016 21:26:07 GMT",
                "Body": six.BytesIO(b'foo\n')
            },
            {}
        ]

        file_path = self.files.create_file('foo.txt', '')
        key_path = self.files.create_file('foo.key', '')
        with open(key_path, 'wb') as f:
            f.write(
                b'K\xc9G\xe1\xf9&\xee\xd1\x03\xf3\xd4\x10\x18o9E\xc2\xaeD'
                b'\x89(\x18\xea\xda\xf6\x81\xc3\xd2\x9d\\\xa8\xe6'
            )
        cmdline = (
            '%s s3://bucket-one/key.txt s3://bucket/key.txt '
            '--sse-c-copy-source --sse-c-copy-source-key fileb://%s' % (
                self.prefix, key_path
            )
        )
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 2)
        self.assertEqual(self.operations_called[0][0].name, 'HeadObject')
        self.assertEqual(self.operations_called[1][0].name, 'CopyObject')

        expected_args = {
            'Key': 'key.txt', 'Bucket': 'bucket',
            'ContentType': 'text/plain',
            'CopySource': 'bucket-one/key.txt',
            'CopySourceSSECustomerAlgorithm': 'AES256',
            'CopySourceSSECustomerKey': (
                'S8lH4fkm7tED89QQGG85RcKuRIkoGOra9oHD0p1cqOY='
            ),
            'CopySourceSSECustomerKeyMD5': 'mL8/mshNgBObhAC1j5BOLw==',
        }
        self.assertDictEqual(self.operations_called[1][1], expected_args)


    # Note ideally the kms sse with a key id would be integration tests
    # However, you cannot delete kms keys so there would be no way to clean
    # up the tests
    def test_cp_upload_with_sse_kms_and_key_id(self):
        full_path = self.files.create_file('foo.txt', 'contents')
        cmdline = (
            '%s %s s3://bucket/key.txt --sse aws:kms --sse-kms-key-id foo' % (
                self.prefix, full_path))
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 1)
        self.assertEqual(self.operations_called[0][0].name, 'PutObject')
        self.assertDictEqual(
            self.operations_called[0][1],
            {'Key': 'key.txt', 'Bucket': 'bucket',
             'ContentType': 'text/plain', 'Body': mock.ANY,
             'SSEKMSKeyId': 'foo', 'ServerSideEncryption': 'aws:kms'}
        )

    def test_cp_upload_large_file_with_sse_kms_and_key_id(self):
        self.parsed_responses = [
            {'UploadId': 'foo'},  # CreateMultipartUpload
            {'ETag': '"foo"'},  # UploadPart
            {'ETag': '"foo"'},  # UploadPart
            {}  # CompleteMultipartUpload
        ]
        full_path = self.files.create_file('foo.txt', 'a' * 10 * (1024 ** 2))
        cmdline = (
            '%s %s s3://bucket/key.txt --sse aws:kms --sse-kms-key-id foo' % (
                self.prefix, full_path))
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 4)

        # We are only really concerned that the CreateMultipartUpload
        # used the KMS key id.
        self.assertEqual(
            self.operations_called[0][0].name, 'CreateMultipartUpload')
        self.assertDictEqual(
            self.operations_called[0][1],
            {'Key': 'key.txt', 'Bucket': 'bucket',
             'ContentType': 'text/plain',
             'SSEKMSKeyId': 'foo', 'ServerSideEncryption': 'aws:kms'}
        )

    def test_cp_copy_with_sse_kms_and_key_id(self):
        self.parsed_responses = [
            {'ContentLength': 5, 'LastModified': '00:00:00Z'},  # HeadObject
            {}  # CopyObject
        ]
        cmdline = (
            '%s s3://bucket/key1.txt s3://bucket/key2.txt '
            '--sse aws:kms --sse-kms-key-id foo' % self.prefix)
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 2)
        self.assertEqual(self.operations_called[1][0].name, 'CopyObject')
        self.assertDictEqual(
            self.operations_called[1][1],
            {'Key': 'key2.txt', 'Bucket': 'bucket',
             'ContentType': 'text/plain', 'CopySource': 'bucket/key1.txt',
             'SSEKMSKeyId': 'foo', 'ServerSideEncryption': 'aws:kms'}
        )

    def test_cp_copy_large_file_with_sse_kms_and_key_id(self):
        self.parsed_responses = [
            {'ContentLength': 10 * (1024 ** 2),
             'LastModified': '00:00:00Z'},  # HeadObject
            {'UploadId': 'foo'},  # CreateMultipartUpload
            {'CopyPartResult': {'ETag': '"foo"'}},  # UploadPartCopy
            {'CopyPartResult': {'ETag': '"foo"'}},  # UploadPartCopy
            {}  # CompleteMultipartUpload
        ]
        cmdline = (
            '%s s3://bucket/key1.txt s3://bucket/key2.txt '
            '--sse aws:kms --sse-kms-key-id foo' % self.prefix)
        self.run_cmd(cmdline, expected_rc=0)
        self.assertEqual(len(self.operations_called), 5)

        # We are only really concerned that the CreateMultipartUpload
        # used the KMS key id.
        self.assertEqual(
            self.operations_called[1][0].name, 'CreateMultipartUpload')
        self.assertDictEqual(
            self.operations_called[1][1],
            {'Key': 'key2.txt', 'Bucket': 'bucket',
             'ContentType': 'text/plain',
             'SSEKMSKeyId': 'foo', 'ServerSideEncryption': 'aws:kms'}
        )

    def test_cannot_use_recursive_with_stream(self):
        cmdline = '%s - s3://bucket/key.txt --recursive' % self.prefix
        _, stderr, _ = self.run_cmd(cmdline, expected_rc=255)
        self.assertIn(
            'Streaming currently is only compatible with non-recursive cp '
            'commands', stderr)

    def test_upload_unicode_path(self):
        self.parsed_responses = [
            {'ContentLength': 10,
             'LastModified': '00:00:00Z'},  # HeadObject
            {'ETag': '"foo"'}  # PutObject
        ]
        command = u's3 cp s3://bucket/\u2603 s3://bucket/\u2713'
        stdout, stderr, rc = self.run_cmd(command, expected_rc=0)

        success_message = (
            u'copy: s3://bucket/\u2603 to s3://bucket/\u2713'
        )
        self.assertIn(success_message, stdout)

        progress_message = 'Completed 10 Bytes'
        self.assertIn(progress_message, stdout)


    @skip_if_windows("Unreadable file is hard to make on windows")
    def test_cp_with_error_and_warning_unreadable_file(self):
        command = "s3 cp --recursive %s s3://bucket/"
        self.parsed_responses = [{
            'Error': {
                'Code': 'NoSuchBucket',
                'Message': 'The specified bucket does not exist',
                'BucketName': 'bucket'
            }
        }]
        self.http_response.status_code = 404

        unreadable_path = self.files.create_file('foo.txt', 'foo')
        self.files.create_file('bar.txt', 'bar')
        os.chmod(unreadable_path, 0o222)
        _, stderr, rc = self.run_cmd(command % self.files.rootdir, expected_rc=1)
        self.assertIn('upload failed', stderr)
        self.assertIn('warning: Skipping file', stderr)
        self.assertIn('File/Directory is not readable.', stderr)

    @skip_if_macos("On MacOS we cannot create an invalid timestamp.")
    def test_cp_with_error_and_warning_invalid_timestamp(self):
        command = "s3 cp %s s3://bucket/foo.txt"
        self.parsed_responses = [{
            'Error': {
                'Code': 'NoSuchBucket',
                'Message': 'The specified bucket does not exist',
                'BucketName': 'bucket'
            }
        }]
        self.http_response.status_code = 404

        full_path = self.files.create_file('foo.txt', 'bar')
        set_invalid_utime(full_path)
        _, stderr, rc = self.run_cmd(command % full_path, expected_rc=1)
        self.assertIn('upload failed', stderr)
        self.assertIn('warning: File has an invalid timestamp.', stderr)


class TestStreamingCPCommand(BaseAWSCommandParamsTest):
    def test_streaming_upload(self):
        command = "s3 cp - s3://bucket/streaming.txt"
        self.parsed_responses = [{
            'ETag': '"c8afdb36c52cf4727836669019e69222"'
        }]

        binary_stdin = BufferedBytesIO(b'foo\n')
        with mock.patch('sys.stdin', binary_stdin):
            self.run_cmd(command)

        self.assertEqual(len(self.operations_called), 1)
        model, args = self.operations_called[0]
        expected_args = {
            'Bucket': 'bucket',
            'Key': 'streaming.txt',
            'Body': mock.ANY
        }

        self.assertEqual(model.name, 'PutObject')
        self.assertEqual(args, expected_args)

    def test_streaming_upload_with_expected_size(self):
        command = "s3 cp - s3://bucket/streaming.txt --expected-size 4"
        self.parsed_responses = [{
            'ETag': '"c8afdb36c52cf4727836669019e69222"'
        }]

        binary_stdin = BufferedBytesIO(b'foo\n')
        with mock.patch('sys.stdin', binary_stdin):
            self.run_cmd(command)

        self.assertEqual(len(self.operations_called), 1)
        model, args = self.operations_called[0]
        expected_args = {
            'Bucket': 'bucket',
            'Key': 'streaming.txt',
            'Body': mock.ANY
        }

        self.assertEqual(model.name, 'PutObject')
        self.assertEqual(args, expected_args)

    def test_streaming_upload_error(self):
        command = "s3 cp - s3://bucket/streaming.txt"
        self.parsed_responses = [{
            'Error': {
                'Code': 'NoSuchBucket',
                'Message': 'The specified bucket does not exist',
                'BucketName': 'bucket'
            }
        }]
        self.http_response.status_code = 404

        binary_stdin = BufferedBytesIO(b'foo\n')
        with mock.patch('sys.stdin', binary_stdin):
            _, stderr, _ = self.run_cmd(command, expected_rc=1)

        error_message = (
            'An error occurred (NoSuchBucket) when calling '
            'the PutObject operation: The specified bucket does not exist'
        )
        self.assertIn(error_message, stderr)

    def test_streaming_upload_when_stdin_unavailable(self):
        command = "s3 cp - s3://bucket/streaming.txt"
        self.parsed_responses = [{
            'ETag': '"c8afdb36c52cf4727836669019e69222"'
        }]

        with mock.patch('sys.stdin', None):
            _, stderr, _ = self.run_cmd(command, expected_rc=1)

        expected_message = (
            'stdin is required for this operation, but is not available'
        )
        self.assertIn(expected_message, stderr)

    def test_streaming_download(self):
        command = "s3 cp s3://bucket/streaming.txt -"
        self.parsed_responses = [
            {
                "AcceptRanges": "bytes",
                "LastModified": "Tue, 12 Jul 2016 21:26:07 GMT",
                "ContentLength": 4,
                "ETag": '"d3b07384d113edec49eaa6238ad5ff00"',
                "Metadata": {},
                "ContentType": "binary/octet-stream"
            },
            {
                "AcceptRanges": "bytes",
                "Metadata": {},
                "ContentType": "binary/octet-stream",
                "ContentLength": 4,
                "ETag": '"d3b07384d113edec49eaa6238ad5ff00"',
                "LastModified": "Tue, 12 Jul 2016 21:26:07 GMT",
                "Body": six.BytesIO(b'foo\n')
            }
        ]

        stdout, stderr, rc = self.run_cmd(command)
        self.assertEqual(stdout, 'foo\n')

        # Ensures no extra operations were called
        self.assertEqual(len(self.operations_called), 2)
        ops = [op[0].name for op in self.operations_called]
        expected_ops = ['HeadObject', 'GetObject']
        self.assertEqual(ops, expected_ops)

    def test_streaming_download_error(self):
        command = "s3 cp s3://bucket/streaming.txt -"
        self.parsed_responses = [{
            'Error': {
                'Code': 'NoSuchBucket',
                'Message': 'The specified bucket does not exist',
                'BucketName': 'bucket'
            }
        }]
        self.http_response.status_code = 404

        _, stderr, _ = self.run_cmd(command, expected_rc=1)
        error_message = (
            'An error occurred (NoSuchBucket) when calling '
            'the HeadObject operation: The specified bucket does not exist'
        )
        self.assertIn(error_message, stderr)


class TestCpCommandWithRequesterPayer(BaseCPCommandTest):
    def test_single_upload(self):
        full_path = self.files.create_file('myfile', 'mycontent')
        cmdline = (
            '%s %s s3://mybucket/mykey --request-payer' % (
                self.prefix, full_path
            )
        )
        self.run_cmd(cmdline, expected_rc=0)
        self.assert_operations_called(
            [
                ('PutObject', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                    'Body': mock.ANY,
                })
            ]
        )

    def test_multipart_upload(self):
        full_path = self.files.create_file('myfile', 'a' * 10 * (1024 ** 2))
        cmdline = (
            '%s %s s3://mybucket/mykey --request-payer' % (
                self.prefix, full_path))

        self.parsed_responses = [
            {'UploadId': 'myid'},      # CreateMultipartUpload
            {'ETag': '"myetag"'},      # UploadPart
            {'ETag': '"myetag"'},      # UploadPart
            {}                         # CompleteMultipartUpload
        ]
        self.run_cmd(cmdline, expected_rc=0)
        self.assert_operations_called(
            [
                ('CreateMultipartUpload', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                }),
                ('UploadPart', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                    'UploadId': 'myid',
                    'PartNumber': mock.ANY,
                    'Body': mock.ANY,
                }),
                ('UploadPart', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                    'UploadId': 'myid',
                    'PartNumber': mock.ANY,
                    'Body': mock.ANY,

                }),
                ('CompleteMultipartUpload', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                    'UploadId': 'myid',
                    'MultipartUpload': {'Parts': [
                        {'ETag': '"myetag"', 'PartNumber': 1},
                        {'ETag': '"myetag"', 'PartNumber': 2}]
                    }
                })
            ]
        )

    def test_recursive_upload(self):
        self.files.create_file('myfile', 'mycontent')
        cmdline = (
            '%s %s s3://mybucket/ --request-payer --recursive' % (
                self.prefix, self.files.rootdir
            )
        )
        self.run_cmd(cmdline, expected_rc=0)
        self.assert_operations_called(
            [
                ('PutObject', {
                    'Bucket': 'mybucket',
                    'Key': 'myfile',
                    'RequestPayer': 'requester',
                    'Body': mock.ANY,
                })
            ]
        )

    def test_single_download(self):
        cmdline = '%s s3://mybucket/mykey %s --request-payer' % (
            self.prefix, self.files.rootdir)

        self.parsed_responses = [
            {"ContentLength": 100, "LastModified": "00:00:00Z"},
            {'ETag': '"foo-1"', 'Body': six.BytesIO(b'foo')},
        ]

        self.run_cmd(cmdline, expected_rc=0)
        self.assert_operations_called(
            [
                ('HeadObject', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                }),
                ('GetObject', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                })
            ]
        )

    def test_ranged_download(self):
        cmdline = '%s s3://mybucket/mykey %s --request-payer' % (
            self.prefix, self.files.rootdir)

        self.parsed_responses = [
            {"ContentLength": 10 * (1024 ** 2), "LastModified": "00:00:00Z"},
            {'ETag': '"foo-1"', 'Body': six.BytesIO(b'foo')},
            {'ETag': '"foo-1"', 'Body': six.BytesIO(b'foo')}
        ]

        self.run_cmd(cmdline, expected_rc=0)
        self.assert_operations_called(
            [
                ('HeadObject', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                }),
                ('GetObject', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                    'Range': mock.ANY,
                }),
                ('GetObject', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                    'Range': mock.ANY,
                })
            ]
        )

    def test_recursive_download(self):
        cmdline = '%s s3://mybucket/ %s --request-payer --recursive' % (
            self.prefix, self.files.rootdir)
        self.parsed_responses = [
            {
                'Contents': [
                    {'Key': 'mykey',
                     'LastModified': '00:00:00Z',
                     'Size': 100},
                ],
                'CommonPrefixes': []
            },
            {'ETag': '"foo-1"', 'Body': six.BytesIO(b'foo')},
        ]
        self.run_cmd(cmdline, expected_rc=0)
        self.assert_operations_called(
            [
                ('ListObjectsV2', {
                    'Bucket': 'mybucket',
                    'Prefix': '',
                    'EncodingType': 'url',
                    'RequestPayer': 'requester',
                }),
                ('GetObject', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester',
                })
            ]
        )

    def test_single_copy(self):
        cmdline = self.prefix
        cmdline += ' s3://sourcebucket/sourcekey s3://mybucket/mykey'
        cmdline += ' --request-payer'
        self.parsed_responses = [
            {'ContentLength': 5, 'LastModified': '00:00:00Z'},
            {}
        ]
        self.run_cmd(cmdline, expected_rc=0)
        self.assert_operations_called(
            [
                ('HeadObject', {
                    'Bucket': 'sourcebucket',
                    'Key': 'sourcekey',
                    'RequestPayer': 'requester',
                }),
                ('CopyObject', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'CopySource': 'sourcebucket/sourcekey',
                    'RequestPayer': 'requester',
                })
            ]
        )

    def test_multipart_copy(self):
        cmdline = self.prefix
        cmdline += ' s3://sourcebucket/sourcekey s3://mybucket/mykey'
        cmdline += ' --request-payer'
        self.parsed_responses = [
            {'ContentLength': 10 * (1024 ** 2),
             'LastModified': '00:00:00Z'},           # HeadObject
            {'UploadId': 'myid'},                    # CreateMultipartUpload
            {'CopyPartResult': {'ETag': '"etag"'}},  # UploadPartCopy
            {'CopyPartResult': {'ETag': '"etag"'}},  # UploadPartCopy
            {}                                       # CompleteMultipartUpload
        ]
        self.run_cmd(cmdline, expected_rc=0)
        self.assert_operations_called(
            [
                ('HeadObject', {
                    'Bucket': 'sourcebucket',
                    'Key': 'sourcekey',
                    'RequestPayer': 'requester',
                }),
                ('CreateMultipartUpload', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'RequestPayer': 'requester'
                }),
                ('UploadPartCopy', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'CopySource': 'sourcebucket/sourcekey',
                    'UploadId': 'myid',
                    'RequestPayer': 'requester',
                    'PartNumber': mock.ANY,
                    'CopySourceRange': mock.ANY,

                }),
                ('UploadPartCopy', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'CopySource': 'sourcebucket/sourcekey',
                    'UploadId': 'myid',
                    'RequestPayer': 'requester',
                    'PartNumber': mock.ANY,
                    'CopySourceRange': mock.ANY,
                }),
                ('CompleteMultipartUpload', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'UploadId': 'myid',
                    'RequestPayer': 'requester',
                    'MultipartUpload': {'Parts': [
                        {'ETag': '"etag"', 'PartNumber': 1},
                        {'ETag': '"etag"', 'PartNumber': 2}]
                    }
                })
            ]
        )

    def test_recursive_copy(self):
        cmdline = self.prefix
        cmdline += ' s3://sourcebucket/ s3://mybucket/'
        cmdline += ' --request-payer'
        cmdline += ' --recursive'
        self.parsed_responses = [
            {
                'Contents': [
                    {'Key': 'mykey',
                     'LastModified': '00:00:00Z',
                     'Size': 100},
                ],
                'CommonPrefixes': []
            },
            {},
        ]
        self.run_cmd(cmdline, expected_rc=0)
        self.assert_operations_called(
            [
                ('ListObjectsV2', {
                    'Bucket': 'sourcebucket',
                    'Prefix': '',
                    'EncodingType': 'url',
                    'RequestPayer': 'requester',
                }),
                ('CopyObject', {
                    'Bucket': 'mybucket',
                    'Key': 'mykey',
                    'CopySource': 'sourcebucket/mykey',
                    'RequestPayer': 'requester',
                })
            ]
        )
