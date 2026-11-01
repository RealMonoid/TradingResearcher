"""Opt-in exact paired-reference projection; not a live worker/profile adapter.

The original source must be authorized before rendering or paging. Existing
scalar views and pinned runtime sources are imported without modification.
"""
from ..codec import Invalid, canonical, digest
from ..context_views import (FEEDBACK_VIEW_PROFILE, MIN_DEFERRED_BYTES,
                             MAX_SECTION_ITEMS, _section,
                             source_view as legacy_source_view)

PROFILE = 'discovery-paired-feedback-view/1'
OWNED_SCHEMAS = (
    ('paired-development-feedback-manifest/1', 'paired_descriptive_feedback_only'),
    ('paired-breakout-development-feedback-manifest/1', 'paired_breakout_descriptive_feedback_only'),
)
REFERENCE_TOOL = {
    'name': 'read_paired_feedback_references',
    'description': (
        'Read an exact ordered page from a deferred reference list in an authorized '
        'paired development-feedback manifest. Use the exact marker path, including '
        'a decimal record index when present. At most 64 items and 16384 UTF-8 '
        'result bytes; no referenced ID is followed. Full authorized read_source '
        'remains available. Pages and repeated inputs count against the same frozen '
        'budget; unread lists remain unread.'),
    'parameters': {'type': 'object', 'properties': {
        'artifact_id': {'type': 'string'},
        'path': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 3, 'maxItems': 4},
        'offset': {'type': 'integer', 'minimum': 0},
        'limit': {'type': 'integer', 'minimum': 1, 'maximum': MAX_SECTION_ITEMS}},
        'required': ['artifact_id', 'path', 'offset', 'limit'], 'additionalProperties': False},
}


def _reference_lists(artifact):
    """Enumerate only existing reference paths of the two exact owned types."""
    if (type(artifact) is not dict
            or any(artifact.get(key) != value for key, value in {
                'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': 'development'}.items())
            or type(artifact.get('body')) is not dict
            or (artifact['body'].get('schema'), artifact.get('authority')) not in OWNED_SCHEMAS):
        return []
    body = artifact['body']
    entries = []
    if type(body.get('cohort')) is dict:
        entries.append((('body', 'cohort', 'artifact_ids'), body['cohort'], 'artifact_ids'))
    if type(body.get('retained_research_records')) is list:
        for index, record in enumerate(body['retained_research_records']):
            if type(record) is dict:
                for key in ('source_refs', 'exposure'):
                    entries.append((('body', 'retained_research_records', str(index), key), record, key))
    return [(path, parent, key) for path, parent, key in entries
            if type(parent.get(key)) is list and all(type(value) is str for value in parent[key])]


def source_view(artifact):
    """Detached candidate view; it confers neither source access nor runtime admission."""
    view = legacy_source_view(artifact, profile=FEEDBACK_VIEW_PROFILE)
    for path, parent, key in _reference_lists(view['content']):
        values = parent[key]
        if len(canonical(values).encode('utf-8')) >= MIN_DEFERRED_BYTES:
            parent[key] = {'schema': 'deferred-source-list/1', 'path': list(path),
                           'count': len(values), 'sha256': digest(values),
                           'tool': REFERENCE_TOOL['name']}
    view['schema'] = PROFILE
    return view


def reference_section(artifact, path, offset, limit):
    """Exact bounded page; caller MUST first authorize the original artifact."""
    if type(path) is not list or len(path) > 4 or any(type(key) is not str for key in path):
        raise Invalid('Unsupported paired reference path')
    for allowed, parent, key in _reference_lists(artifact):
        if tuple(path) == allowed:
            return _section(artifact, path, parent[key], offset, limit)
    raise Invalid('Unsupported paired reference path')


def read_references(client, lease, arguments):
    """Access-first tool primitive, to be bound by a future qualified worker.

    No RPC/tool registration or profile acceptance is added by this function.
    The client retains current context, lease and source-revocation enforcement.
    """
    if type(arguments) is not dict or set(arguments) != {'artifact_id', 'path', 'offset', 'limit'}:
        raise Invalid('Exact paired reference arguments required')
    artifact = client.call('read_artifact', lease=lease, artifact_id=arguments['artifact_id'])
    return reference_section(artifact, arguments['path'], arguments['offset'], arguments['limit'])
