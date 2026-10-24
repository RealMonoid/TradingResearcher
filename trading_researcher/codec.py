"""Bounded canonical JSON for local-coordination/1.0 (not an RFC 8785 claim)."""
import hashlib
import json

MAX_BYTES = 1_048_576


class Invalid(ValueError):
    """The request does not satisfy the local operational contract."""


def canonical(value):
    def check(item, depth=0):
        if depth > 40:
            raise Invalid('JSON nesting exceeds 40 levels')
        if item is None or type(item) in (bool, int, str):
            return
        if type(item) is list:
            for child in item:
                check(child, depth + 1)
            return
        if type(item) is dict:
            for key, child in item.items():
                if type(key) is not str or not key.isascii():
                    raise Invalid('JSON keys must be ASCII strings')
                check(child, depth + 1)
            return
        raise Invalid('Use explicit decimal strings instead of floating-point JSON numbers')
    check(value)
    result = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if len(result.encode('utf-8')) > MAX_BYTES:
        raise Invalid('Payload exceeds the local 1 MiB limit')
    return result


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Invalid('Duplicate JSON key')
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=pairs)
        canonical(value)
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Invalid(str(exc)) from exc


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def text(value, name):
    if type(value) is not str or not value.strip() or len(value) > 8192:
        raise Invalid(f'{name} must be a nonempty bounded string')
    return value


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise Invalid(f'{name} must be an integer >= {minimum}')
    return value


def strings(value, name):
    if type(value) is not list or len(value) > 256:
        raise Invalid(f'{name} must be a list with at most 256 strings')
    for item in value:
        text(item, name)
    if len(set(value)) != len(value):
        raise Invalid(f'{name} contains duplicates')
    return value
