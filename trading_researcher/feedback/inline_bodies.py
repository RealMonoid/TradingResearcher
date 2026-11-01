"""Inactive exact JSON body table and narrowly typed ancestry pages.

All source reads must be authorized by the caller. This module does not install
a worker/profile, choose sources, summarize content or grant research admission.
"""
import re

from ..codec import Invalid, canonical, decode, digest, text
from ..context_views import MIN_DEFERRED_BYTES, MAX_SECTION_ITEMS, _lookup, _section
from .reference_views import OWNED_SCHEMAS as PAIRED_SCHEMAS, source_view

SCHEMA = 'discovery-feedback-inline-bodies/1'
BODY_REF = 'inline-feedback-body-ref/1'
MANIFESTS = (('development-feedback-manifest/1', 'descriptive_development_feedback_only'), *PAIRED_SCHEMAS)
RECORD_FIELDS = {'id', 'creator', 'authority', 'body', 'source_refs', 'exposure'}
ANCESTRY_PATHS = tuple(('body', 'evidence_at_publication', 'data_use', 'prior_knowledge', key)
                       for key in ('artifact_ids', 'context_ids'))
ANCESTRY_TOOL = {
    'name': 'read_feedback_ancestry_references',
    'description': (
        'Read an exact ordered page from either marked prior-knowledge artifact_ids '
        'or context_ids list in an authorized paired breakout feedback manifest. '
        'Use the exact five-component marker path. At most 64 items and 16384 '
        'UTF-8 result bytes; neither artifact nor context IDs are followed. Full '
        'authorized read_source remains available. Pages and repeated inputs count '
        'against the frozen budget; unread lists remain unread.'),
    'parameters': {'type': 'object', 'properties': {
        'artifact_id': {'type': 'string'},
        'path': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 5, 'maxItems': 5},
        'offset': {'type': 'integer', 'minimum': 0},
        'limit': {'type': 'integer', 'minimum': 1, 'maximum': MAX_SECTION_ITEMS}},
        'required': ['artifact_id', 'path', 'offset', 'limit'], 'additionalProperties': False},
}


def require(condition, message):
    if not condition:
        raise Invalid(message)


def _identity(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None


def _owned(artifact):
    return (type(artifact) is dict and all(artifact.get(key) == value for key, value in {
        'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
        'data_class': 'development'}.items()) and type(artifact.get('body')) is dict
        and (artifact['body'].get('schema'), artifact.get('authority')) in MANIFESTS)


def _record(record):
    return (type(record) is dict and set(record) == RECORD_FIELDS and _identity(record['id'])
        and type(record['creator']) is str and type(record['authority']) is str
        and type(record['body']) is dict and record['body'].get('schema') == 'research-record/1'
        and record['body'].get('kind') in ('idea', 'gap')
        and all(type(record[key]) is list and all(type(ref) is str for ref in record[key])
                for key in ('source_refs', 'exposure')))


def _ancestry_lists(artifact):
    if (not _owned(artifact)
            or artifact['body']['schema'] != 'paired-breakout-development-feedback-manifest/1'
            or artifact['authority'] != 'paired_breakout_descriptive_feedback_only'):
        return []
    evidence = artifact['body'].get('evidence_at_publication')
    data_use = evidence.get('data_use') if type(evidence) is dict else None
    if type(data_use) is not dict or data_use.get('schema') != 'paired-data-use-assessment/1':
        return []
    result = []
    for path in ANCESTRY_PATHS:
        try:
            values = _lookup(artifact, path)
        except Invalid:
            continue
        if all(_identity(value) for value in values):
            result.append((path, values))
    return result


def _views(sources):
    require(type(sources) is list, 'Explicit original source list required')
    identities = [source.get('id') if type(source) is dict else None for source in sources]
    require(all(_identity(identity) for identity in identities) and len(set(identities)) == len(identities),
            'Unique original artifact identities required')
    views = [source_view(source) for source in sources]
    for view, original in zip(views, sources, strict=True):
        for path, values in _ancestry_lists(original):
            if len(canonical(values).encode('utf-8')) < MIN_DEFERRED_BYTES:
                continue
            parent = view['content']
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = {'schema': 'deferred-source-list/1', 'path': list(path),
                'count': len(values), 'sha256': digest(values), 'tool': ANCESTRY_TOOL['name']}
    return views


def build(purpose, sources):
    """Build a detached candidate. Complete unique bodies stay initially inline."""
    text(purpose, 'discovery purpose')
    views = _views(sources)
    table, originals = {}, {}
    for view, source in zip(views, sources, strict=True):
        if not _owned(source) or type(source['body'].get('retained_research_records')) is not list:
            continue
        for index, original in enumerate(source['body']['retained_research_records']):
            require(not (type(original) is dict and type(original.get('body')) is dict
                         and original['body'].get('schema') == BODY_REF),
                    'Reserved inline-body tag collision: representation gap; original source retained')
            if type(original) is dict and _identity(original.get('id')):
                identity = original['id']
                encoded = canonical(original)
                require(identity not in originals or originals[identity] == encoded,
                        'Conflicting immutable retained record identity')
                originals[identity] = encoded
            if not _record(original):
                continue
            projected = view['content']['body']['retained_research_records'][index]
            require(canonical(projected['body']) == canonical(original['body']),
                    'Base source presentation changed a substantive body')
            identity = original['id']; body_hash = digest(original['body'])
            table[identity] = {'body_sha256': body_hash, 'body': original['body']}
            projected['body'] = {'schema': BODY_REF, 'record_id': identity, 'body_sha256': body_hash}
    packet = {'schema': SCHEMA, 'purpose': purpose, 'sources': views, 'inline_record_bodies': table}
    return decode(canonical(packet))


def expand(packet):
    """Expand only the inline body table; ancestry markers remain for exact pages.

    Structural consistency is not source authentication. verify() binds the
    expanded values to caller-authorized original sources before use.
    """
    require(type(packet) is dict and set(packet) == {'schema', 'purpose', 'sources', 'inline_record_bodies'}
            and packet['schema'] == SCHEMA and type(packet['sources']) is list
            and type(packet['inline_record_bodies']) is dict, 'Exact inline-body packet required')
    text(packet['purpose'], 'discovery purpose')
    detached = decode(canonical(packet))
    table = detached['inline_record_bodies']
    for identity, entry in table.items():
        require(_identity(identity) and type(entry) is dict and set(entry) == {'body_sha256', 'body'}
                and type(entry['body']) is dict and entry['body'].get('schema') == 'research-record/1'
                and entry['body'].get('kind') in ('idea', 'gap')
                and _identity(entry['body_sha256']) and digest(entry['body']) == entry['body_sha256'],
                'Invalid inline body identity, value or digest')
    used = set()
    for view in detached['sources']:
        require(type(view) is dict and type(view.get('content')) is dict, 'Source view required')
        source = view['content']
        if not _owned(source) or type(source['body'].get('retained_research_records')) is not list:
            continue
        for record in source['body']['retained_research_records']:
            if type(record) is not dict or type(record.get('body')) is not dict or record['body'].get('schema') != BODY_REF:
                continue
            pointer = record['body']
            require(set(record) == RECORD_FIELDS and set(pointer) == {'schema', 'record_id', 'body_sha256'}
                    and _identity(record['id']) and pointer['record_id'] == record['id']
                    and pointer['record_id'] in table
                    and pointer['body_sha256'] == table[pointer['record_id']]['body_sha256'],
                    'Invalid, missing or mismatched inline body target')
            used.add(pointer['record_id'])
            # Separate objects preserve independence of every expanded occurrence.
            record['body'] = decode(canonical(table[pointer['record_id']]['body']))
    require(used == set(table), 'Unreferenced inline body target')
    return {'purpose': detached['purpose'], 'sources': detached['sources']}


def verify(packet, purpose, sources):
    """Bind expansion to complete originals already authorized by the caller."""
    expanded = expand(packet)
    expected = {'purpose': purpose, 'sources': _views(sources)}
    require(canonical(expanded) == canonical(expected), 'Expanded packet differs from authorized sources')
    require(canonical(packet) == canonical(build(purpose, sources)),
            'Packet differs from canonical exact body-table representation')
    return expanded


def ancestry_section(artifact, path, offset, limit):
    """Exact two-path page only; caller must first authorize the original."""
    require(type(path) is list and all(type(key) is str for key in path)
            and tuple(path) in ANCESTRY_PATHS, 'Unsupported feedback ancestry path')
    for allowed, values in _ancestry_lists(artifact):
        if tuple(path) == allowed:
            return _section(artifact, path, values, offset, limit)
    raise Invalid('Owned typed feedback ancestry list required')


def read_ancestry(client, lease, arguments):
    """Future tool primitive: authenticate parent on every call, follow no IDs."""
    require(type(arguments) is dict and set(arguments) == {'artifact_id', 'path', 'offset', 'limit'},
            'Exact feedback ancestry arguments required')
    artifact = client.call('read_artifact', lease=lease, artifact_id=arguments['artifact_id'])
    return ancestry_section(artifact, arguments['path'], arguments['offset'], arguments['limit'])
