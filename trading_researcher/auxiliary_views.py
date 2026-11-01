"""Opt-in lossless auxiliary provenance transport, without retrieval or omission."""
from copy import deepcopy
import hashlib
from pathlib import Path

from .codec import Invalid, canonical, digest

PROFILE = 'auxiliary-provenance-dictionary/1'
REUSE_SCOPE = 'bounded-math-reuse/1.0'
REUSE_PATH = 'docs/architecture/20_BOUNDED_MATH_REUSE.md'
REUSE_SHA256 = '62cdb38908176ef91fe3368a8c41cdbd10a3f808499aa316e1ed863cf161a569'
EXPLANATION = ('Only top-level artifact source_refs and exposure lists use reference_indices into '
    'reference_dictionary (zero-based). Expand each index to its exact string in its original order. '
    'All original reference values, source bodies, qualifications and other fields are present. '
    'This is a lossless transport encoding, not source approval or a scientific conclusion.')


def _require(condition, message):
    if not condition:
        raise Invalid(message)


def _artifacts(packet):
    _require(type(packet) is dict, 'Expected an auxiliary packet')
    if packet.get('schema') == 'formalization-input/1':
        values = packet.get('sources')
        _require(type(values) is list, 'Expected complete formalization sources')
    elif packet.get('schema') == 'semantic-review-input/1':
        definitions = packet.get('definitions')
        _require(type(definitions) is list, 'Expected complete review definitions')
        values = [packet.get('formalization'), packet.get('catalog'), *definitions]
        if 'data_target' in packet:
            values.append(packet['data_target'])
    else:
        raise Invalid('Unsupported auxiliary packet schema')
    _require(all(type(value) is dict and {'id', 'body', 'source_refs', 'exposure'} <= set(value)
                 for value in values), 'Expected full source envelopes')
    return values


def activation_contract(scope):
    _require(scope == REUSE_SCOPE, 'Unsupported bounded-math activation scope')
    try:
        raw = (Path(__file__).resolve().parents[1] / REUSE_PATH).read_bytes()
        _require(hashlib.sha256(raw).hexdigest() == REUSE_SHA256, 'Activation contract differs from its approved source')
        text = raw.decode('utf-8')
    except (OSError, UnicodeError) as exc:
        raise Invalid('Approved activation contract is unavailable') from exc
    return {'schema': REUSE_SCOPE, 'path': REUSE_PATH, 'sha256': REUSE_SHA256, 'text': text}


def present(packet, *, bounded_math_scope=None):
    """Bodies remain verbatim; deduplicate only reference strings in metadata."""
    canonical(packet)
    original = _artifacts(packet)
    for artifact in original:
        for field in ('source_refs', 'exposure'):
            _require(type(artifact[field]) is list and all(type(ref) is str for ref in artifact[field]),
                     'Expected string reference lists')
    refs = sorted({ref for artifact in original for field in ('source_refs', 'exposure') for ref in artifact[field]})
    index = {ref: n for n, ref in enumerate(refs)}
    packed = deepcopy(packet)
    for artifact in _artifacts(packed):
        for field in ('source_refs', 'exposure'):
            artifact[field] = {'reference_indices': [index[ref] for ref in artifact[field]]}
    result = {'schema': PROFILE, 'reference_dictionary': refs, 'source_packet': packed,
              'source_packet_sha256': digest(packet), 'interpretation': EXPLANATION}
    if bounded_math_scope is not None:
        result['activation_contract'] = activation_contract(bounded_math_scope)
    canonical(result)
    # Admission invariant, not a quality or model-comprehension assertion.
    _require(canonical(restore(result)) == canonical(packet), 'Reference transport changed the source packet')
    return result


def restore(view):
    canonical(view)
    required = {'schema', 'reference_dictionary', 'source_packet', 'source_packet_sha256', 'interpretation'}
    _require(type(view) is dict and required <= set(view) <= required | {'activation_contract'} and view['schema'] == PROFILE
             and view['interpretation'] == EXPLANATION, 'Unsupported reference transport')
    if 'activation_contract' in view:
        _require(view['activation_contract'] == activation_contract(REUSE_SCOPE), 'Activation contract was modified')
    refs = view['reference_dictionary']
    _require(type(refs) is list and all(type(ref) is str for ref in refs), 'Invalid reference dictionary')
    _require(refs == sorted(set(refs)), 'Reference dictionary must be unique and sorted')
    packet = deepcopy(view['source_packet'])
    used = set()
    for artifact in _artifacts(packet):
        for field in ('source_refs', 'exposure'):
            marker = artifact[field]
            _require(type(marker) is dict and set(marker) == {'reference_indices'}
                     and type(marker['reference_indices']) is list, 'Invalid reference encoding')
            positions = marker['reference_indices']
            _require(all(type(i) is int and 0 <= i < len(refs) for i in positions), 'Invalid reference index')
            used.update(positions)
            artifact[field] = [refs[i] for i in positions]
    _require(used == set(range(len(refs))), 'Unreferenced dictionary entry')
    _require(digest(packet) == view['source_packet_sha256'], 'Restored auxiliary packet hash differs')
    return packet
