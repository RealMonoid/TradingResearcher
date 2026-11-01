"""Opt-in, deterministic source presentation; no source selection or authority.

The controller still reads and retains the full original artifact. Explicit
provenance/reference arrays can be deferred; no model summarizes them.
This changes presentation, not the data supplied to any scientific calculator.
"""
from .codec import Invalid, canonical, decode, digest


VIEW_VERSION = 'discovery-source-view/1'
TOOL_VIEW_PROFILE = 'discovery-source-view/2'
FEEDBACK_VIEW_PROFILE = 'discovery-source-view/3'
PRESENTATION_PROFILES = (VIEW_VERSION, TOOL_VIEW_PROFILE, FEEDBACK_VIEW_PROFILE)
DEFER_PATHS = (
    ('exposure',), ('source_refs',),
    ('body', 'manifest', 'provenance', 'checksum_evidence_refs'),
    ('body', 'manifest', 'provenance', 'raw_source_refs'),
    ('body', 'manifest', 'provenance', 'source_uris'),
)
MIN_DEFERRED_BYTES = 1024
MAX_SECTION_ITEMS = 64
MAX_SECTION_BYTES = 16384

SECTION_TOOL = {
    'name': 'read_source_section',
    'description': (
        'Read an exact ordered slice of an authorized source provenance/reference list. '
        'Use the path in a deferred-source-list marker; at most 64 items and 16384 UTF-8 '
        'result bytes. No reference or URL is followed. Full read_source remains available; '
        'both reads and accumulated results remain subject to the frozen token budget.'),
    'parameters': {'type': 'object', 'properties': {
        'artifact_id': {'type': 'string'},
        'path': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 1, 'maxItems': 4},
        'offset': {'type': 'integer', 'minimum': 0},
        'limit': {'type': 'integer', 'minimum': 1, 'maximum': MAX_SECTION_ITEMS}},
        'required': ['artifact_id', 'path', 'offset', 'limit'], 'additionalProperties': False},
}

FEEDBACK_SECTION_TOOL = {
    'name': 'read_feedback_references',
    'description': (
        'Read an exact ordered page from a deferred reference list in an authorized '
        'development-feedback manifest. Use the exact marker path, including a decimal '
        'record index when present. At most 64 items and 16384 UTF-8 result bytes; '
        'no referenced ID is followed. Full read_source remains available. Pages and '
        'repeated inputs count against the same frozen budget; unread lists remain unread.'),
    'parameters': {'type': 'object', 'properties': {
        'artifact_id': {'type': 'string'},
        'path': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 3, 'maxItems': 4},
        'offset': {'type': 'integer', 'minimum': 0},
        'limit': {'type': 'integer', 'minimum': 1, 'maximum': MAX_SECTION_ITEMS}},
        'required': ['artifact_id', 'path', 'offset', 'limit'], 'additionalProperties': False},
}


def _feedback_lists(artifact):
    """Exact owned-envelope shape only; this is not an authorization check."""
    if (type(artifact) is not dict or any(artifact.get(key) != value for key, value in {
            'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
            'data_class': 'development', 'authority': 'descriptive_development_feedback_only'}.items())
            or type(artifact.get('body')) is not dict
            or artifact['body'].get('schema') != 'development-feedback-manifest/1'):
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


def _lookup(artifact, path):
    value = artifact
    for key in path:
        if type(value) is not dict or key not in value:
            raise Invalid('Source list path unavailable')
        value = value[key]
    if type(value) is not list:
        raise Invalid('Source list path unavailable')
    return value


def source_view(artifact, profile=VIEW_VERSION):
    """Render a detached view after the caller has authenticated the full read."""
    if profile not in PRESENTATION_PROFILES:
        raise Invalid('Unsupported source presentation profile')
    projected = decode(canonical(artifact))
    for path in DEFER_PATHS:
        try:
            values = _lookup(projected, path)
        except Invalid:
            continue
        if len(canonical(values).encode('utf-8')) < MIN_DEFERRED_BYTES:
            continue
        parent = projected
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = {
            'schema': 'deferred-source-list/1', 'path': list(path),
            'count': len(values), 'sha256': digest(values), 'tool': 'read_source_section',
        }
    if profile == FEEDBACK_VIEW_PROFILE:
        for path, parent, key in _feedback_lists(projected):
            values = parent[key]
            if len(canonical(values).encode('utf-8')) >= MIN_DEFERRED_BYTES:
                parent[key] = {'schema': 'deferred-source-list/1', 'path': list(path),
                               'count': len(values), 'sha256': digest(values),
                               'tool': 'read_feedback_references'}
    qualification = (
        'Content is a projection, not the hash-identical original envelope. '
        'Deferred lists are unread evidence, not empty or irrelevant evidence. '
        'Read required entries with read_source_section; preserve gaps if budgets prevent access. '
        'Original source and inherited exposure remain retained; referenced IDs grant no additional access.')
    if profile == FEEDBACK_VIEW_PROFILE:
        qualification = qualification.replace('with read_source_section', 'with the tool named by each marker')
    return {
        'schema': FEEDBACK_VIEW_PROFILE if profile == FEEDBACK_VIEW_PROFILE else VIEW_VERSION,
        'artifact_id': artifact['id'], 'content': projected,
        'qualification': qualification,
    }


def source_section(artifact, path, offset, limit):
    """Exact list page only. The caller MUST authorize the original artifact first."""
    if (type(path) is not list or len(path) > 4 or
            any(type(key) is not str for key in path) or tuple(path) not in DEFER_PATHS):
        raise Invalid('Unsupported source list path')
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= MAX_SECTION_ITEMS:
        raise Invalid('Source section requires bounded integer controls')
    values = _lookup(artifact, path)
    return _section(artifact, path, values, offset, limit)


def feedback_source_section(artifact, path, offset, limit):
    """Page the authorized original; never traverse an arbitrary path or ID."""
    if type(path) is not list or len(path) > 4 or any(type(key) is not str for key in path):
        raise Invalid('Unsupported feedback reference path')
    for allowed, parent, key in _feedback_lists(artifact):
        if tuple(path) == allowed:
            return _section(artifact, path, parent[key], offset, limit)
    raise Invalid('Unsupported feedback reference path')


def _section(artifact, path, values, offset, limit):
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= MAX_SECTION_ITEMS:
        raise Invalid('Source section requires bounded integer controls')
    if offset > len(values):
        raise Invalid('Source section offset exceeds list length')
    end = min(offset + limit, len(values))
    result = {
        'schema': 'source-section/1', 'artifact_id': artifact['id'], 'path': list(path),
        'list_sha256': digest(values), 'count': len(values), 'offset': offset,
        'next_offset': end if end < len(values) else None, 'values': values[offset:end],
    }
    encoded = canonical(result)
    if len(encoded.encode('utf-8')) > MAX_SECTION_BYTES:
        raise Invalid('Source section exceeds byte bound; request fewer items or retain an access gap')
    return decode(encoded)
