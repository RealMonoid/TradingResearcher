"""Independent lossless-retention oracles, fixed before implementation review.

Codec fixtures are exact bytes, not statistical or market observations. Family
framing substitutes the calculator output and does not replace actual replay.
"""
from copy import deepcopy
import gzip
import hashlib
import io
import unittest
from unittest.mock import patch
import zlib

import test_family_oracles as family_source
from trading_researcher.codec import Invalid, canonical
from trading_researcher.family_pipeline import calculate_family
from trading_researcher.study_stream import (
    MAX_DECODED_BYTES, EncodedStream, validate_stream, decode_stream,
)


EMPTY = bytes.fromhex('1f8b08000000000000ff03000000000000000000')
HELLO = bytes.fromhex('1f8b08000000000000ffcb48cdc9c9e7020020303a3606000000')


def descriptor(raw):
    return {'schema':'study-stream-gzip/1', 'compression':{'name':'gzip', 'level':6, 'mtime':0,
        'filename':'', 'zlib_version':zlib.ZLIB_VERSION, 'zlib_runtime_version':zlib.ZLIB_RUNTIME_VERSION},
        'decoded_blob':{'sha256':hashlib.sha256(raw).hexdigest(), 'size':len(raw)}}


def encode(chunks, *, encoded_limit=1024 * 1024, decoded_limit=1024 * 1024):
    stream = io.BytesIO()
    writer = EncodedStream(stream, encoded_limit=encoded_limit, decoded_limit=decoded_limit)
    for chunk in chunks:
        writer.write(chunk)
    metadata = writer.finish()
    return stream.getvalue(), metadata, stream


class StudyStreamIndependentTests(unittest.TestCase):
    def test_exact_empty_and_hello_oracles_and_metadata(self):
        self.assertEqual(MAX_DECODED_BYTES, 256 * 1024**2)
        for raw, expected in ((b'', EMPTY), (b'hello\n', HELLO)):
            with self.subTest(raw=raw):
                encoded, metadata, stream = encode([raw])
                self.assertEqual(encoded, expected)
                self.assertEqual(metadata, descriptor(raw))
                self.assertFalse(stream.closed)
                self.assertIsNone(validate_stream(expected, metadata))
                self.assertEqual(decode_stream(expected, metadata), raw)

    def test_write_fragmentation_does_not_change_retained_encoding(self):
        raw = b'{"kind":"draw","value":null}\n' * 4096
        whole = encode([raw])
        fragmented = encode([raw[index:index + 17] for index in range(0, len(raw), 17)])
        self.assertEqual(whole[:2], fragmented[:2])
        self.assertEqual(decode_stream(fragmented[0], fragmented[1]), raw)

    def test_fragmented_encoding_matches_separate_gzipfile_reference(self):
        raw = b'{"kind":"draw","value":null}\n' * 4096
        stream = io.BytesIO()
        with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0, compresslevel=6) as writer:
            for index in range(0, len(raw), 65536):
                writer.write(raw[index:index + 65536])
                # Python 3.14 adds its own BufferedWriter. Flushing only that
                # input buffer fixes compressor chunking without Z_SYNC_FLUSH.
                # This is a version-bound independent stdlib reference, not a
                # claim of equality to arbitrary GzipFile buffering policies.
                writer._buffer.flush()
        expected = stream.getvalue()
        for size in (len(raw), 17):
            chunks = [raw[index:index + size] for index in range(0, len(raw), size)]
            observed, metadata, _ = encode(chunks)
            self.assertEqual(observed, expected)
            self.assertEqual(decode_stream(expected, metadata), raw)

    def test_high_entropy_chunk_boundaries_have_one_fixed_encoding(self):
        from trading_researcher.study_stream import INPUT_CHUNK_BYTES
        self.assertEqual(INPUT_CHUNK_BYTES, 65536)
        raw = b''.join(hashlib.sha256(index.to_bytes(4, 'big')).digest() for index in range(6200))
        partitions = [[raw], [raw[:65535], raw[65535:65536], raw[65536:65537], raw[65537:131072], raw[131072:]],
                      [raw[index:index + 997] for index in range(0, len(raw), 997)]]
        streams = [encode(chunks) for chunks in partitions]
        self.assertEqual(streams[0][:2], streams[1][:2])
        self.assertEqual(streams[0][:2], streams[2][:2])
        stream = io.BytesIO()
        with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0, compresslevel=6) as writer:
            for index in range(0, len(raw), 65536):
                writer.write(raw[index:index + 65536]); writer._buffer.flush()
        self.assertEqual(streams[0][0], stream.getvalue())
        self.assertEqual(decode_stream(streams[0][0], streams[0][1]), raw)

    def test_replay_compares_encoded_bytes_and_checks_exact_eof(self):
        reader = io.BytesIO(HELLO)
        replay = EncodedStream(reader, encoded_limit=100, decoded_limit=100, verify=True)
        replay.write(b'he'); replay.write(b'llo\n')
        self.assertEqual(replay.finish(), descriptor(b'hello\n'))
        self.assertFalse(reader.closed)
        for changed in (HELLO[:-1], HELLO + b'x', bytes([HELLO[0] ^ 1]) + HELLO[1:]):
            with self.subTest(changed=changed), self.assertRaises(Invalid):
                replay = EncodedStream(io.BytesIO(changed), encoded_limit=100, decoded_limit=100, verify=True)
                replay.write(b'hello\n'); replay.finish()

    def test_header_must_be_canonical_even_when_gzip_payload_still_decodes(self):
        for offset, value in ((3, 1), (4, 1), (8, 2), (9, 3)):
            changed = bytearray(HELLO); changed[offset] = value
            with self.subTest(offset=offset), self.assertRaises(Invalid):
                validate_stream(bytes(changed), descriptor(b'hello\n'))
        # An optional empty filename is a different header, even though the
        # uncompressed content and CRC are identical and standard gzip allows it.
        changed = HELLO[:3] + b'\x08' + HELLO[4:10] + b'\x00' + HELLO[10:]
        with self.assertRaises(Invalid):
            decode_stream(changed, descriptor(b'hello\n'))

    def test_bit_corruption_and_every_truncation_are_rejected(self):
        for offset in (10, 13, len(HELLO) - 8, len(HELLO) - 4):
            changed = bytearray(HELLO); changed[offset] ^= 0x80
            with self.subTest(offset=offset), self.assertRaises(Invalid):
                validate_stream(bytes(changed), descriptor(b'hello\n'))
        for length in range(len(HELLO)):
            with self.subTest(length=length), self.assertRaises(Invalid):
                decode_stream(HELLO[:length], descriptor(b'hello\n'))

    def test_concat_members_and_trailing_zero_or_junk_are_rejected(self):
        for suffix in (EMPTY, HELLO, b'\x00', b'\x00' * 16, b'arbitrary suffix'):
            with self.subTest(suffix=suffix), self.assertRaises(Invalid):
                validate_stream(HELLO + suffix, descriptor(b'hello\n'))

    def test_decoded_hash_and_size_are_both_verified(self):
        original = descriptor(b'hello\n')
        for changes in ({'size':5}, {'size':7}, {'sha256':'0' * 64}):
            changed = deepcopy(original); changed['decoded_blob'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(Invalid):
                decode_stream(HELLO, changed)

    def test_descriptor_exact_shapes_types_and_runtime_binding(self):
        original = descriptor(b'hello\n'); invalid = []
        for top in ({}, {'schema':'study-stream-gzip/2'}, {'extra':'forbidden'}):
            invalid.append(top if not top else {**deepcopy(original), **top})
        for key, value in (('name','deflate'), ('level',9), ('mtime',False), ('filename',None),
                           ('zlib_version','unbound'), ('zlib_runtime_version','unbound'), ('extra',0)):
            changed = deepcopy(original); changed['compression'][key] = value; invalid.append(changed)
        for key, value in (('size',True), ('size',-1), ('size','6'), ('sha256',None),
                           ('sha256','a' * 63), ('extra',1)):
            changed = deepcopy(original); changed['decoded_blob'][key] = value; invalid.append(changed)
        for changed in invalid:
            with self.subTest(descriptor=changed), self.assertRaises(Invalid):
                validate_stream(HELLO, changed)

    def test_decoded_expansion_limit_is_checked_before_large_allocation(self):
        raw = b'X' * (1024 * 1024)
        encoded, metadata, _ = encode([raw])
        self.assertLess(len(encoded), 2048)
        for operation in (decode_stream, validate_stream):
            with self.subTest(operation=operation.__name__), self.assertRaises(Invalid):
                operation(encoded, metadata, encoded_limit=2048, decoded_limit=64)
            # A forged small declaration must also be checked during expansion,
            # not merely rejected because honest metadata exceeds the limit.
            with self.subTest(operation=operation.__name__, forged_small_descriptor=True), self.assertRaises(Invalid):
                operation(encoded, descriptor(b'X' * 64), encoded_limit=2048, decoded_limit=64)
        self.assertEqual(decode_stream(HELLO, descriptor(b'hello\n'), decoded_limit=6), b'hello\n')
        with self.assertRaises(Invalid):
            decode_stream(HELLO, descriptor(b'hello\n'), decoded_limit=5)

    def test_encoded_limit_includes_header_footer_and_replay_reads(self):
        encoded, metadata, _ = encode([b'hello\n'], encoded_limit=len(HELLO), decoded_limit=6)
        self.assertEqual(encoded, HELLO)
        with self.assertRaises(Invalid):
            encode([b'hello\n'], encoded_limit=len(HELLO) - 1)
        with self.assertRaises(Invalid):
            validate_stream(HELLO, metadata, encoded_limit=len(HELLO) - 1)
        with self.assertRaises(Invalid):
            replay = EncodedStream(io.BytesIO(HELLO), encoded_limit=len(HELLO) - 1, verify=True)
            replay.write(b'hello\n'); replay.finish()

    def test_failed_write_preserves_prefix_and_does_not_close_supplied_stream(self):
        stream = io.BytesIO()
        writer = EncodedStream(stream, encoded_limit=100, decoded_limit=5)
        with self.assertRaises(Invalid):
            writer.write(b'hello\n')
        self.assertFalse(stream.closed)
        self.assertTrue(stream.getvalue().startswith(HELLO[:10]))
        prefix = io.BytesIO()
        with self.assertRaises(Invalid):
            writer = EncodedStream(prefix, encoded_limit=10, decoded_limit=100)
            writer.write(b'hello\n'); writer.finish()
        self.assertFalse(prefix.closed)
        self.assertEqual(prefix.getvalue(), HELLO[:10])

    def test_finalization_is_once_and_post_finish_writes_are_invalid(self):
        stream = io.BytesIO(); writer = EncodedStream(stream, encoded_limit=100)
        writer.write(b'hello\n'); writer.finish()
        before = stream.getvalue()
        with self.assertRaises(Invalid): writer.finish()
        with self.assertRaises(Invalid): writer.write(b'new input')
        self.assertEqual(stream.getvalue(), before)

    def test_strict_bytes_and_limit_types(self):
        for value in ('hello', bytearray(b'hello'), None, 4):
            with self.subTest(value=value), self.assertRaises(Invalid):
                EncodedStream(io.BytesIO(), encoded_limit=100).write(value)
        for changes in ({'encoded_limit':True}, {'encoded_limit':-1},
                        {'decoded_limit':True}, {'decoded_limit':-1}, {'verify':1}):
            with self.subTest(changes=changes), self.assertRaises(Invalid):
                EncodedStream(io.BytesIO(), **{'encoded_limit':100, **changes})
        with self.assertRaises(Invalid):
            validate_stream(bytearray(HELLO), descriptor(b'hello\n'))


class FamilyByteFramingIndependentTests(unittest.TestCase):
    def payload(self):
        report, model = family_source.source_and_model()
        identities = ['a"\\\n\u2603', 'b\t\u00e9']
        return {'report':{k:v for k,v in report.items() if k != 'cases'}, 'diagnostics':model['diagnostics'],
            'specification':model['specification'], 'effects':model['effects'],
            'components':[{'id':identity, 'scenario':index + 1} for index,identity in enumerate(identities)],
            'time_rows':8, 'seed':37, 'bootstrap_seed':41, 'limits':{'max_seconds':2},
            'design':{'primary_count':2, 'base_length':4,
                'mc_policy':{'schema':'mc-boundary-policy/1', 'noncoverage':family_source.rational(1,20),
                    'delta':family_source.rational(1,20), 'direction':'positive'}}}, report['cases']

    def test_complete_framed_bytes_equal_dictionary_path_with_escaped_ids(self):
        payload, cases = self.payload(); before = deepcopy((payload, cases))
        draw = {'schema':'joint-bootstrap-draw/1', 'index':0, 'length':4, 'value':None,
            'scope_count':3, 'condition_count':1, 'segments':2, 'path_sha256':'1' * 64}
        modes = []
        def fake_calculate(report, design, limits, **callbacks):
            dictionary, binary = callbacks.get('on_draw'), callbacks.get('on_draw_bytes')
            self.assertNotEqual(dictionary is None, binary is None)
            modes.append('bytes' if binary is not None else 'dictionary')
            if binary is None: dictionary(deepcopy(draw))
            else: binary(canonical(draw).encode())
            return {'status':'COMPUTED_UNCALIBRATED',
                'interval':{'lower':family_source.rational(0), 'upper':family_source.rational(1,5)},
                'monte_carlo':{'nominal_classification':'TESTED_INCONCLUSIVE', 'boundary_stable':True}}
        dictionary, binary = [], []
        with patch('trading_researcher.family_pipeline.calculate', side_effect=fake_calculate):
            first = calculate_family(payload, cases, lambda item: dictionary.append((canonical(item) + '\n').encode()))
            second = calculate_family(payload, cases, lambda item: binary.append((canonical(item) + '\n').encode()),
                retain_draw_bytes=binary.append)
        self.assertEqual(first, second)
        self.assertEqual(binary, dictionary)
        self.assertEqual(modes, ['dictionary', 'dictionary', 'bytes', 'bytes'])
        draw_lines = [line for line in binary if b'"kind":"draw"' in line]
        self.assertEqual(draw_lines, [(canonical({'kind':'draw', 'response_id':item['id'], 'value':draw}) + '\n').encode()
                                     for item in payload['components']])
        self.assertEqual((payload, cases), before)

    def test_encoded_callback_exception_is_not_swallowed(self):
        payload, cases = self.payload(); retained = []
        def fake_calculate(report, design, limits, **callbacks):
            callbacks['on_draw_bytes'](b'{"value":null}')
            raise AssertionError('Calculator continued after rejected draw retention')
        def reject(line):
            retained.append(line)
            raise Invalid('Fixed byte sink failure')
        with patch('trading_researcher.family_pipeline.calculate', side_effect=fake_calculate):
            with self.assertRaisesRegex(Invalid, 'Fixed byte sink failure'):
                calculate_family(payload, cases, lambda item:None, retain_draw_bytes=reject)
        self.assertEqual(len(retained), 1)
        self.assertTrue(retained[0].endswith(b'\n'))


if __name__ == '__main__':
    unittest.main()
