"""Synthetic acceptance demonstration through real RPC; no LLM or market claim."""
import json
import shutil
import time

from .coordination import Broker
from .server import Client


def run_memory_demo(admin, url, directory):
    credential = admin.call('register_worker', name='researcher', role='discovery',
                            capabilities=['research-record/v1'])
    source = admin.call('add_research', kind='source',
                        content={'text': 'Synthetic development observation', 'uri': 'fixture:memory-demo'},
                        scope={'instrument': 'fixture'}, source_refs=[])
    context = admin.call('create_context', role='discovery', epoch=1, artifact_ids=[source['id']])
    job = admin.call('enqueue', key='memory-demo', spec={
        'kind': 'research-record/v1', 'context_id': context['id'],
        'purpose': 'Synthetic journal and retrieval demonstration', 'allowed_workers': ['researcher'],
        'max_attempts': 1, 'lease_seconds': 30, 'deadline': int(time.time()) + 60, 'dependencies': []})
    worker = Client(url, credential['token'])
    lease = worker.call('claim')['lease']
    worker.call('search_memory', lease=lease, query='development')
    args = {'lease': lease, 'scope': {'instrument': 'fixture'}, 'source_refs': [source['id']]}
    first = worker.call('record_research', kind='idea', content={'text': 'First untested interpretation'}, **args)
    worker.call('record_research', kind='gap',
                content={'text': 'A needed measurement is absent', 'reason': 'Missing implementation',
                         'reopen_condition': 'Independent feature certification'}, **args)
    corrected = worker.call('record_research', kind='idea',
                            content={'text': 'Corrected untested interpretation'},
                            relations={'supersedes': [first['id']]}, **args)
    completion = worker.call('submit', lease=lease, artifact_id=corrected['id'])
    batch = admin.call('inspect', job_id=job['id'])['batch_id']
    released = admin.call('release_batch', batch_id=batch, target_epoch=2)
    admin.call('create_context', role='discovery', epoch=2,
               artifact_ids=[source['id'], *released['artifact_ids']])
    before = admin.call('inspect_memory')
    admin.call('rebuild_memory')
    if admin.call('inspect_memory') != before:
        raise RuntimeError('Projection replay changed the journal')
    backup = directory / 'memory-demo-backup.sqlite3'
    admin.call('backup', destination=str(backup))
    restored = directory / 'restore-check'
    restored.mkdir()
    shutil.copy2(backup, restored / 'registry.sqlite3')
    shutil.copy2(directory / 'operator.key', restored / 'operator.key')
    copy = Broker(restored)
    try:
        restored_matches = copy.call(copy.admin_token, 'inspect_memory') == before
    finally:
        copy.close()
    if not restored_matches:
        raise RuntimeError('Restored journal differs from the source')
    report = {'scope': 'Synthetic research memory and operational checks only; no scientific evidence',
              'completion': completion, 'memory_records': before['total'],
              'correction_preserved': {first['id'], corrected['id']} <= {r['id'] for r in before['records']},
              'market_findings': admin.call('inspect_memory', view='market_model')['total'],
              'restored_projection_matches': restored_matches, 'integrity': admin.call('verify'),
              'directory': str(directory.resolve())}
    (directory / 'memory-demo-result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report
