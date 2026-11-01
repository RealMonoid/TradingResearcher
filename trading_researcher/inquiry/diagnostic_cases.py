"""Small DQ behavioral case kit using existing source/context and research APIs.

No provider dispatch, budget creation, semantic grader, or scientific authority.
Operator-only expectations precede calls; the worker receives synthetic facts.
Use the normal admitted run_research_once (or qualified successor) for execution.
"""
from copy import deepcopy
from pathlib import Path
import time

from ..codec import Invalid, canonical, decode, digest, integer


FIXTURES = Path(__file__).with_name('fixtures')
VERSION = 'diagnostic-cases/1'
PURPOSE = ('Continue the supplied synthetic investigation. Retain the relevant findings, '
           'interpretation and warranted next action in the existing research records. '
           'Use only the supplied facts and permitted tools; preserve the original question.')


def _require(value, message):
    if not value:
        raise Invalid(message)


def _suite():
    inputs = decode((FIXTURES / 'diagnostic_inputs_v1.json').read_text(encoding='utf-8'))
    answers = decode((FIXTURES / 'diagnostic_expectations_v1.json').read_text(encoding='utf-8'))
    _require(inputs['version'] == answers['version'] == VERSION, 'Diagnostic suite version mismatch')
    _require(set(inputs['cases']) == set(answers['cases']), 'Diagnostic case/expectation mismatch')
    return inputs, answers


def case_ids():
    return list(_suite()[0]['cases'])


def model_input(case_id):
    inputs, _ = _suite()
    _require(type(case_id) is str and case_id in inputs['cases'], 'Unknown diagnostic case')
    return {'purpose': PURPOSE, 'facts': deepcopy(inputs['cases'][case_id])}


def expectations(case_id):
    model_input(case_id)
    return deepcopy(_suite()[1]['cases'][case_id])


def prepare_case(admin, case_id, profile, *, epoch):
    """Retain one input, private expectations and context; create no call/grant/job.

    Use a dedicated test registry and the existing authenticated operator client.
    Caller retains admission, provider authentication and shared funding duties.
    All facts are initially visible: this v1 tests no first-exposure timing claim.
    """
    integer(epoch, 'epoch')
    packet = model_input(case_id)
    inputs, answers = _suite()
    criteria = expectations(case_id)
    # Validate before any write; large existing profiles are committed by hash.
    profile_hash = digest(profile)
    source = admin.call('add_research', kind='source',
        content={'text': canonical(packet['facts']), 'uri': 'fixture:work-item'},
        scope={'purpose': 'synthetic diagnostic exercise'}, source_refs=[])['id']
    research_time = int(time.time())
    envelope = {'version': 'local-context/2', 'role': 'discovery', 'epoch': epoch,
                'artifact_ids': [source], 'exposure': [source], 'research_time': research_time}
    context = admin.call('create_context', role='discovery', epoch=epoch,
        artifact_ids=[source], research_time=research_time)['id']
    _require(context == digest(envelope), 'Unexpected diagnostic context closure')
    plan = {'schema': VERSION, 'case_id': case_id, 'suite_sha256': digest([inputs, answers]),
            'profile_sha256': profile_hash, 'context': envelope, 'source_id': source,
            'model_input_sha256': digest(packet), **criteria}
    private = admin.call('add_research', kind='source',
        content={'text': canonical(plan), 'uri': 'fixture:private-review'},
        scope={'purpose': 'operator-only diagnostic expectation'}, source_refs=[],
        data_class='assessment')['id']
    return {'plan_id': private, 'source_id': source, 'context_id': context}


def collect_case(admin, prepared, *, epoch_id):
    """Return auditable calls and a blank semantic review, never an inferred pass.

    The operator evaluates criteria against fixed facts and cited transcript
    spans. Agreement/filled fields are not a semantic check. Retain the registry
    for job state, tool-result artifacts and attempts, including stopped jobs.
    """
    _require(type(prepared) is dict and set(prepared) == {'plan_id', 'source_id', 'context_id'},
             'Expected exact prepared case handles')
    artifact = admin.call('get_artifact', artifact_id=prepared['plan_id'])
    _require(artifact['data_class'] == 'assessment', 'Expectations must be protected')
    plan = decode(artifact['body']['content']['text'])
    _require(plan['schema'] == VERSION, 'Unknown diagnostic plan')
    _require(plan['suite_sha256'] == digest(list(_suite())), 'Different fixed diagnostic suite')
    expected = expectations(plan['case_id'])
    _require(all(plan.get(key) == value for key, value in expected.items()),
             'Diagnostic expectations differ from the fixed suite')
    _require(plan['source_id'] == prepared['source_id']
             and digest(plan['context']) == prepared['context_id'], 'Diagnostic context changed')
    source = admin.call('get_artifact', artifact_id=prepared['source_id'])
    packet = {'purpose': PURPOSE, 'facts': decode(source['body']['content']['text'])}
    _require(packet == model_input(plan['case_id'])
             and digest(packet) == plan['model_input_sha256'], 'Diagnostic input changed')
    retained = admin.call('inspect_research_epoch', epoch_id=epoch_id)
    request = retained['request']
    _require(request['context_id'] == prepared['context_id'], 'Different diagnostic context')
    _require(digest(request['profile']) == plan['profile_sha256'], 'Different diagnostic profile')
    _require(artifact['body']['created_at'] <= retained['created_at'], 'Expectations postdate epoch')
    # Request/response and usage data come from the controller, not model assertions.
    calls = retained['calls']
    perspectives = {worker: {'call_count': 0, 'job_ids': []} for worker in request['workers']}
    jobs = {}
    for call in calls:
        job_id = call['job_id']
        if job_id not in jobs:
            jobs[job_id] = admin.call('inspect', job_id=job_id)
        job = jobs[job_id]
        _require(job['spec']['purpose'] == PURPOSE, 'Unexpected diagnostic work instruction')
        for worker in job['spec']['allowed_workers']:
            _require(worker in perspectives, 'Unexpected diagnostic perspective')
            perspectives[worker]['call_count'] += 1
            if job_id not in perspectives[worker]['job_ids']:
                perspectives[worker]['job_ids'].append(job_id)
    return {'schema': 'diagnostic-observation/1', 'case_id': plan['case_id'],
            'suite_sha256': plan['suite_sha256'], 'profile_sha256': plan['profile_sha256'],
            'prepared': deepcopy(prepared), 'epoch_id': epoch_id,
            'execution_kind': ('SCRIPTED_CONTROL_ONLY' if request['profile']['mode'] == 'fixture'
                               else 'PROVIDER_AUTHENTICATION_REQUIRES_REVIEW'),
            'behavioral_assessment': 'NOT_ASSESSED', 'call_count': len(calls),
            'perspectives': perspectives, 'calls': calls, 'jobs_with_calls': jobs,
            'usage': retained['usage'], 'unknown_usage_calls': sum(c['usage_unknown'] for c in calls),
            'review': [{'criterion': criterion, 'judgment': 'NOT_ASSESSED',
                        'evidence_refs': [], 'reason': ''} for criterion in plan['criteria']],
            'limits': ['All case facts were initially available; no prospective-purpose timing proof.',
                       'Provider mode and complete records do not authenticate model reasoning.',
                       'No general reliability, comparative improvement or economic claim.']}


def summarize(reports):
    """Keep unrun cases visible; this inventory never computes behavioral passes."""
    states = {case: 'NOT_RUN' for case in case_ids()}
    seen, bindings = set(), set()
    for report in reports:
        case = report['case_id']
        _require(case in states and case not in seen, 'Unknown or duplicate diagnostic case')
        _require(report['schema'] == 'diagnostic-observation/1'
                 and report['behavioral_assessment'] == 'NOT_ASSESSED', 'Use original ungraded observations')
        seen.add(case)
        bindings.add((report['suite_sha256'], report['profile_sha256']))
        states[case] = 'CALLS_AWAITING_REVIEW' if report['call_count'] else 'NO_CALLS'
    _require(len(bindings) <= 1, 'Do not pool different suites or profiles')
    return {'schema': 'diagnostic-inventory/1', 'planned_cases': len(states), 'cases': states,
            'behavioral_passes': 0, 'behavioral_assessment': 'NOT_ASSESSED',
            'note': 'Zero assessed passes is not zero correct answers; independent review remains pending.'}
