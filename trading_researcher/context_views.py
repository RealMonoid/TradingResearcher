"""Opt-in, deterministic source presentation; no source selection or authority.

The controller still reads and retains the full original artifact. Only five
explicit provenance/reference arrays can be deferred; no model summarizes them.
This changes presentation, not the data supplied to any scientific calculator.
"""
from .codec import Invalid, canonical, decode, digest


VIEW_VERSION = 'discovery-source-view/1'
TOOL_VIEW_PROFILE = 'discovery-source-view/2'
PRESENTATION_PROFILES = (VIEW_VERSION, TOOL_VIEW_PROFILE)
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


def _lookup(artifact, path):
    value = artifact
    for key in path:
        if type(value) is not dict or key not in value:
            raise Invalid('Source list path unavailable')
        value = value[key]
    if type(value) is not list:
        raise Invalid('Source list path unavailable')
    return value


def source_view(artifact):
    """Render a detached view after the caller has authenticated the full read."""
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
    return {
        'schema': VIEW_VERSION, 'artifact_id': artifact['id'], 'content': projected,
        'qualification': (
            'Content is a projection, not the hash-identical original envelope. '
            'Deferred lists are unread evidence, not empty or irrelevant evidence. '
            'Read required entries with read_source_section; preserve gaps if budgets prevent access. '
            'Original source and inherited exposure remain retained; referenced IDs grant no additional access.'),
    }


def source_section(artifact, path, offset, limit):
    """Exact list page only. The caller MUST authorize the original artifact first."""
    if (type(path) is not list or len(path) > 4 or
            any(type(key) is not str for key in path) or tuple(path) not in DEFER_PATHS):
        raise Invalid('Unsupported source list path')
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= MAX_SECTION_ITEMS:
        raise Invalid('Source section requires bounded integer controls')
    values = _lookup(artifact, path)
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
