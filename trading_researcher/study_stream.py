"""Lossless bounded study transport; canonical decoded records are unchanged."""
import hashlib
import re
import struct
import zlib

from .codec import Invalid
from .evaluation_policy import require


MAX_DECODED_BYTES = 256 * 1024**2
INPUT_CHUNK_BYTES = 65536  # Part of study-stream-gzip/1, independent of caller writes.
COMPRESSION = {'name': 'gzip', 'level': 6, 'mtime': 0, 'filename': '',
    'zlib_version': zlib.ZLIB_VERSION, 'zlib_runtime_version': zlib.ZLIB_RUNTIME_VERSION}
HEADER = bytes.fromhex('1f8b08000000000000ff')


def _limit(value):
    require(type(value) is int and 0 <= value <= MAX_DECODED_BYTES, 'Invalid study stream limit')
    return value


def _encoding(value, decoded_limit):
    require(type(value) is dict and set(value) == {'schema', 'compression', 'decoded_blob'}
        and value['schema'] == 'study-stream-gzip/1', 'Unknown study stream encoding')
    compression = value['compression']
    require(type(compression) is dict and compression == COMPRESSION
        and type(compression['level']) is int and type(compression['mtime']) is int,
        'Unsupported study stream compression')
    blob = value['decoded_blob']
    require(type(blob) is dict and set(blob) == {'sha256', 'size'}
        and type(blob['size']) is int and 0 <= blob['size'] <= decoded_limit
        and type(blob['sha256']) is str and re.fullmatch('[0-9a-f]{64}', blob['sha256']) is not None,
        'Invalid decoded study stream descriptor')
    return blob


class EncodedStream:
    """Generate or compare every gzip byte, including the header and footer."""
    def __init__(self, stream, *, encoded_limit, decoded_limit=MAX_DECODED_BYTES, verify=False):
        self.stream = stream
        self.encoded_limit = _limit(encoded_limit)
        self.decoded_limit = _limit(decoded_limit)
        require(type(verify) is bool, 'Invalid study replay mode')
        self.verify = verify
        self.encoded_size = self.decoded_size = 0
        self.checksum = hashlib.sha256()
        self.crc = 0
        self.pending = bytearray()
        self.finished = False
        self.failed = False
        # Fixed gzip header, raw DEFLATE and CRC/length footer. Unlike a
        # file-owning wrapper, this never writes implicitly during destruction.
        self.compressor = zlib.compressobj(level=6, wbits=-15)
        self._emit(HEADER)

    def _emit(self, data):
        require(not self.failed, 'Study stream already failed')
        try:
            require(self.encoded_size + len(data) <= self.encoded_limit,
                'Study output exceeds its reserved storage')
            if self.verify:
                require(self.stream.read(len(data)) == data, 'Study case/draw replay differs')
            else:
                require(self.stream.write(data) == len(data), 'Incomplete study stream write')
            self.encoded_size += len(data)
            return len(data)
        except Exception:
            self.failed = True
            raise

    def write(self, data):
        require(not self.finished and not self.failed, 'Study stream is closed or failed')
        require(type(data) is bytes, 'Study stream requires exact bytes')
        try:
            require(self.decoded_size + len(data) <= self.decoded_limit,
                'Study stream exceeds decoded computation bound')
            offset = 0
            while offset < len(data):
                end = min(len(data), offset + INPUT_CHUNK_BYTES - len(self.pending))
                self.pending.extend(data[offset:end])
                offset = end
                if len(self.pending) == INPUT_CHUNK_BYTES:
                    self._emit(self.compressor.compress(self.pending))
                    self.pending.clear()
            self.checksum.update(data)
            self.crc = zlib.crc32(data, self.crc)
            self.decoded_size += len(data)
        except Exception:
            self.failed = True
            raise

    def finish(self):
        require(not self.finished and not self.failed, 'Study stream is closed or failed')
        self._emit(self.compressor.compress(self.pending))
        self.pending.clear()
        self._emit(self.compressor.flush(zlib.Z_FINISH))
        self._emit(struct.pack('<II', self.crc, self.decoded_size))
        self.finished = True
        if self.verify:
            require(self.stream.read(1) == b'', 'Study replay has trailing bytes')
        return {'schema': 'study-stream-gzip/1', 'compression': dict(COMPRESSION),
            'decoded_blob': {'sha256': self.checksum.hexdigest(), 'size': self.decoded_size}}


def _decoded(encoded, encoding, encoded_limit, decoded_limit):
    _limit(encoded_limit); _limit(decoded_limit)
    blob = _encoding(encoding, decoded_limit)
    require(type(encoded) is bytes and len(encoded) <= encoded_limit, 'Study encoded stream exceeds bound')
    require(encoded.startswith(HEADER), 'Noncanonical study gzip header')
    decoder = zlib.decompressobj(wbits=31)
    checksum = hashlib.sha256(); total = 0
    try:
        for offset in range(0, len(encoded), 16384):
            pending = encoded[offset:offset+16384]
            require(not decoder.eof, 'Study stream has trailing members or bytes')
            while pending:
                # One extra byte detects expansion past the declared size. No
                # unbounded flush/decompress call can allocate the entire body.
                chunk = decoder.decompress(pending, min(65536, blob['size'] - total + 1))
                total += len(chunk)
                require(total <= blob['size'], 'Study decoded stream exceeds descriptor or bound')
                checksum.update(chunk)
                require(not decoder.unused_data, 'Study stream has trailing members or bytes')
                pending = decoder.unconsumed_tail
                yield chunk
        require(decoder.eof and total == blob['size'] and checksum.hexdigest() == blob['sha256'],
            'Study decoded stream is incomplete or differs')
    except zlib.error as error:
        raise Invalid('Invalid study gzip stream') from error


def validate_stream(encoded, encoding, *, encoded_limit=MAX_DECODED_BYTES, decoded_limit=MAX_DECODED_BYTES):
    for _ in _decoded(encoded, encoding, encoded_limit, decoded_limit): pass


def decode_stream(encoded, encoding, *, encoded_limit=MAX_DECODED_BYTES, decoded_limit=MAX_DECODED_BYTES):
    return b''.join(_decoded(encoded, encoding, encoded_limit, decoded_limit))
