"""Synthetic two-perspective research-loop acceptance through authenticated RPC."""
import json
import time

from .researcher import TOOL_DEFINITIONS, ScriptedProvider, run_research_once
from .server import Client


def run_research_demo(admin, url, directory):
    credentials = {name: admin.call('register_worker', name=name, role='discovery',
                                   capabilities=['research-record/v1']) for name in ('first', 'second')}
    source = admin.call('add_research', kind='source',
                        content={'text': 'Synthetic observation; no market data or empirical result.',
                                 'uri': 'fixture:research-demo'}, scope={}, source_refs=[])
    context = admin.call('create_context', role='discovery', epoch=1, artifact_ids=[source['id']])
    profile = {'model': 'fixture/1', 'prompt_version': 'research-demo/1', 'max_calls': 6,
               'max_tokens': 80000, 'max_seconds': 60, 'max_cost_units': 0, 'currency': 'NONE',
               'mode': 'fixture', 'prompts': {'first': 'Independent first fixture perspective.',
                                             'second': 'Independent second fixture perspective.'},
               'tools': TOOL_DEFINITIONS, 'generation_parameters': {},
               'max_output_tokens': 4096, 'call_timeout_seconds': 10, 'max_retries': 0}
    epoch = admin.call('create_research_epoch', key='demo-epoch', context_id=context['id'],
                       workers=['first', 'second'], profile=profile)
    batch = admin.call('create_batch', key='demo-research-batch', epoch=1)
    for name in credentials:
        admin.call('enqueue', key='demo-' + name, spec={
            'kind': 'research-record/v1', 'context_id': context['id'],
            'purpose': 'Test infrastructure with scripted public output; no scientific claim',
            'allowed_workers': [name], 'max_attempts': 1, 'lease_seconds': 10,
            'deadline': int(time.time()) + 90, 'dependencies': [],
            'batch_id': batch['id'], 'research_epoch_id': epoch['id']})
    admin.call('seal_batch', batch_id=batch['id'])
    fixtures = [
        [{'status': 'tools', 'calls': [{'id': 'lookup', 'name': 'search_memory',
                                       'arguments': {'query': 'Synthetic'}}]},
         {'status': 'final', 'record': {'kind': 'idea',
             'content': {'text': 'Private first fixture hypothesis; not empirical discovery'},
             'scope': {}, 'source_refs': [source['id']]}}],
        [{'status': 'final', 'record': {'kind': 'gap',
             'content': {'text': 'Second fixture requires an unavailable measurement',
                         'reason': 'No certified measurement in this fixture',
                         'reopen_condition': 'Independent measurement certification'},
             'scope': {}, 'source_refs': [source['id']]}}],
    ]
    outcomes = [run_research_once(Client(url, credentials[name]['token']), ScriptedProvider(replies))
                for name, replies in zip(credentials, fixtures)]
    if not all(result['accepted'] for result in outcomes):
        raise RuntimeError('Fixture research job did not complete')
    release = admin.call('release_batch', batch_id=batch['id'], target_epoch=2)
    snapshot = admin.call('inspect_research_epoch', epoch_id=epoch['id'])
    base = [call['request']['messages'][1] for call in snapshot['calls']]
    same_base = all(value == base[0] for value in base)
    isolated = 'Private first fixture hypothesis' not in json.dumps(snapshot['calls'][-1]['request'])
    if not same_base or not isolated:
        raise RuntimeError('Perspective fixture isolation failed')
    report = {'scope': 'Provider-neutral fixture loop; no live LLM, market evaluation, or profitability evidence',
              'genuine_discovery': False, 'perspectives_completed': len(outcomes),
              'same_base_context': same_base, 'private_transcripts': isolated,
              'usage': snapshot['usage'], 'usage_units': 'Synthetic byte-based fixture counts; not provider tokens',
              'outcomes': outcomes, 'release': release, 'integrity': admin.call('verify'),
              'directory': str(directory.resolve())}
    (directory / 'research-demo-result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report
