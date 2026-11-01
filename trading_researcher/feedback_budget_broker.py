"""Opt-in D093 broker. Four preserved D092-era methods only route versioned grants.

The default Broker and all source pins used by existing meaning reviews stay
unchanged. This is static reviewed code, with no runtime patching or evaluation.
"""
import hashlib
import uuid
from pathlib import Path

from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied
from .context_views import SECTION_TOOL, FEEDBACK_SECTION_TOOL, FEEDBACK_VIEW_PROFILE, PRESENTATION_PROFILES
from .research_calls import PROFILE_FIELDS, REQUEST_FIELDS
from .coordination import Broker
from . import complete_feedback_budget

LEGACY_RESEARCH_CALLS_SHA256 = '6284dca04ccbdb47fd14df418aee5d2a78bf634b5174b41fbc94f90281ccf512'


class FeedbackBudgetBroker(Broker):
    def __init__(self, *args, **kwargs):
        actual = hashlib.sha256(Path(__file__).with_name('research_calls.py').read_bytes()).hexdigest()
        if actual != LEGACY_RESEARCH_CALLS_SHA256:
            raise Denied('Opt-in budget broker requires its reviewed legacy dispatch version')
        super().__init__(*args, **kwargs)

    def _research_spec_check(self, spec):
        super()._research_spec_check(spec)
        if 'research_epoch_id' in spec:
            epoch = self._epoch(spec['research_epoch_id'])
            if epoch['request'].get('budget_overlay') == complete_feedback_budget.POLICY:
                complete_feedback_budget.validate_job(self, epoch, spec)

    def _create_research_epoch(self, actor, key, context_id, workers, profile, budget_overlay=None, review_continuation=None):
        text(key, 'epoch request key')
        strings(workers, 'workers')
        if len(workers) != 2:
            raise Invalid('The adopted profile requires two discovery perspectives')
        context = self._context(context_id)
        if context['role'] != 'discovery':
            raise Invalid('A research epoch requires a discovery base snapshot')
        for worker in workers:
            principal = self._db.execute('SELECT role FROM principals WHERE name=?', (worker,)).fetchone()
            if principal is None or principal['role'] != 'discovery':
                raise Invalid('Both perspectives require registered discovery identities')
        optional_fields = {'source_presentation', 'perspective_profiles'}
        if (type(profile) is not dict or not PROFILE_FIELDS <= set(profile)
                or set(profile) - PROFILE_FIELDS - optional_fields):
            raise Invalid('Missing or unexpected epoch profile fields')
        if type(profile['prompts']) is not dict or set(profile['prompts']) != set(workers):
            raise Invalid('Each perspective needs an explicit frozen prompt')
        for prompt in profile['prompts'].values():
            text(prompt, 'perspective prompt')
        if type(profile['tools']) is not list or type(profile['generation_parameters']) is not dict:
            raise Invalid('Tool definitions and generation parameters must be explicit')
        if 'source_presentation' in profile and (
                profile['source_presentation'] not in PRESENTATION_PROFILES or not any(
                    canonical(tool) == canonical(SECTION_TOOL) for tool in profile['tools'])):
            raise Invalid('Source presentation requires the versioned exact section tool')
        feedback_profile = profile.get('source_presentation') == FEEDBACK_VIEW_PROFILE
        if feedback_profile and not any(canonical(tool) == canonical(FEEDBACK_SECTION_TOOL) for tool in profile['tools']):
            raise Invalid('Feedback presentation requires its exact reference section tool')
        if not feedback_profile and any(type(tool) is dict and tool.get('name') == FEEDBACK_SECTION_TOOL['name']
                                        for tool in profile['tools']):
            raise Invalid('Feedback reference sections require the explicit feedback presentation profile')
        token_ceiling = 80000
        if budget_overlay is not None:
            from .epoch_budget_dispatch import validate
            token_ceiling = validate(self, context, profile, budget_overlay)
        for name, ceiling in [('max_calls', 12), ('max_tokens', token_ceiling), ('max_seconds', 1800)]:
            if integer(profile[name], name, 1) > ceiling:
                raise Invalid('Epoch profile exceeds the adopted pilot ceiling')
        integer(profile['max_cost_units'], 'max_cost_units')
        integer(profile['max_output_tokens'], 'max_output_tokens', 1)
        if integer(profile['call_timeout_seconds'], 'call_timeout_seconds', 1) > profile['max_seconds']:
            raise Invalid('Call timeout cannot exceed the epoch limit')
        if integer(profile['max_retries'], 'max_retries') > 2:
            raise Invalid('Transport retries are bounded at two and count as model calls')
        for field in ('model', 'prompt_version', 'currency'):
            text(profile[field], field)
        if profile['mode'] not in ('fixture', 'live'):
            raise Invalid('Unknown provider mode')
        if profile['mode'] == 'live' and (profile['max_cost_units'] == 0 or profile['currency'] == 'NONE'):
            raise Invalid('A live profile requires an explicit positive currency cap')
        if 'perspective_profiles' in profile:
            from .auxiliary import PROFILE_FIELDS as ROLE_FIELDS, validate_profile
            selected = profile['perspective_profiles']
            if type(selected) is not dict or set(selected) != set(workers):
                raise Invalid('Each perspective requires an explicit frozen call profile')
            for worker, settings in selected.items():
                if type(settings) is not dict or set(settings) != ROLE_FIELDS - {'prompt'}:
                    raise Invalid('Perspective call profile has missing or unexpected fields')
                validate_profile({**settings, 'prompt': profile['prompts'][worker]}, profile)
        if review_continuation is not None:
            if budget_overlay is not None:
                raise Invalid('Review continuation cannot reuse another budget grant')
            from .review_continuation import validate
            validate(self, context, profile, review_continuation)
        request = {'context_id': context_id, 'workers': workers, 'profile': profile}
        if budget_overlay is not None:
            request['budget_overlay'] = budget_overlay
        if review_continuation is not None:
            request['review_continuation'] = review_continuation
        old = self._db.execute('SELECT id,request FROM research_epochs WHERE request_key=?', (key,)).fetchone()
        if old:
            if old['request'] != canonical(request):
                raise Conflict('Epoch key already binds a different frozen request')
            if budget_overlay is not None:
                from .epoch_budget_dispatch import inspect
                inspect(self, self._epoch(old['id']))
            if review_continuation is not None:
                from .review_continuation import inspect
                inspect(self, self._epoch(old['id']))
            return {'id': old['id']}
        identity = uuid.uuid4().hex
        created_at = self._now()
        if budget_overlay is not None:
            from .epoch_budget_dispatch import claim
            claim(self, {'id': identity, 'request_key': key, 'request': request, 'created_at': created_at})
        if review_continuation is not None:
            from .review_continuation import claim
            claim(self, {'id': identity, 'request_key': key, 'request': request, 'created_at': created_at})
        self._db.execute('INSERT INTO research_epochs VALUES(?,?,?,?,?)',
                         (identity, key, canonical(request), created_at, 'active'))
        self._event(actor['name'], 'research_epoch_created', epoch_id=identity, request=request)
        return {'id': identity}

    def _reserve_research_call(self, actor, lease, key, request, input_token_bound,
                               output_token_limit, cost_bound_units):
        job = self._owned(actor, lease)
        if 'research_epoch_id' not in job['spec']:
            raise Denied('This job has no frozen research epoch')
        epoch = self._epoch(job['spec']['research_epoch_id'])
        profile = self._effective_research_profile(job)
        text(key, 'call key')
        if type(request) is not dict or set(request) != REQUEST_FIELDS:
            raise Invalid('Malformed normalized provider request')
        if request['model'] != profile['model'] or request['prompt_version'] != profile['prompt_version']:
            raise Invalid('Provider request differs from the frozen epoch profile')
        if type(request['messages']) is not list or type(request['tools']) is not list:
            raise Invalid('Provider messages and tools must be lists')
        expected_system = {'role': 'system', 'content': profile['prompts'][actor['name']]}
        if (not request['messages'] or canonical(request['messages'][0]) != canonical(expected_system)
                or canonical(request['tools']) != canonical(profile['tools'])
                or canonical(request['generation_parameters']) != canonical(profile['generation_parameters'])):
            raise Invalid('Prompt, tools, or generation parameters differ from the frozen profile')
        if 'research_call_profile' in job['spec']:
            from .auxiliary import request_for
            if canonical(request)!=canonical(request_for(job['spec'],self._auxiliary_packet_for_spec(job['spec']))):
                raise Invalid('Auxiliary request differs from its exact frozen input packet')
        integer(input_token_bound, 'input_token_bound', 1)
        integer(output_token_limit, 'output_token_limit', 1)
        integer(cost_bound_units, 'cost_bound_units')
        if output_token_limit != profile['max_output_tokens']:
            raise Invalid('Output limit differs from frozen profile')
        reservation = {'request': request, 'input_bound': input_token_bound,
                       'output_bound': output_token_limit, 'cost_bound': cost_bound_units}
        fingerprint = digest(reservation)
        prior = self._db.execute('''SELECT * FROM research_calls
            WHERE job_id=? AND generation=? AND request_key=?''', (job['id'], job['generation'], key)).fetchone()
        if prior:
            if prior['request_hash'] != fingerprint:
                raise Conflict('Call key already binds a different request or reservation')
            return {'call_id': prior['id'], 'dispatch': False, 'state': prior['state']}
        self._check_feedback_context(self._context(job['spec']['context_id']))
        if 'research_call_profile' in job['spec']:
            calls=self._calls_for(epoch['id'],job['id'],job['generation'])
            if (len(calls)>profile['max_retries'] or any(c['reply'] is not None
                    and c['reply']['response'].get('status') not in ('failed','timeout') for c in calls)):
                raise Denied('Auxiliary retries exceed the frozen transport policy')
        if epoch['state'] != 'active' or self._now() >= epoch['created_at'] + profile['max_seconds']:
            raise Denied('Research epoch is halted or its wall-time budget is exhausted')
        if self._db.execute("SELECT 1 FROM research_calls WHERE epoch_id=? AND state='reserved'", (epoch['id'],)).fetchone():
            raise Denied('An unresolved dispatch must be reconciled before another call')
        usage = self._call_usage(epoch['id'])
        if (usage['calls'] + 1 > profile['max_calls']
                or usage['tokens'] + input_token_bound + output_token_limit > profile['max_tokens']
                or usage['cost_units'] + cost_bound_units > profile['max_cost_units']):
            raise Denied('Research epoch reservation would exceed its frozen budget')
        context = self._context(job['spec']['context_id'])
        deadline=min(job['spec']['deadline'],epoch['created_at']+profile['max_seconds'],
                     self._now()+profile['call_timeout_seconds'])
        stored = self._worker_artifact(actor, job, context,
                                       {'schema': 'provider-call/1', **reservation,'dispatch_deadline':deadline}, [])
        identity = uuid.uuid4().hex
        if 'budget_overlay' in epoch['request']:
            from .epoch_budget_dispatch import reserve
            reserve(self, epoch, job, identity, input_token_bound, output_token_limit, cost_bound_units, request=request)
        if 'review_continuation' in epoch['request']:
            from .review_continuation import reserve
            reserve(self, epoch, job, identity, input_token_bound, output_token_limit, cost_bound_units)
        self._db.execute('''INSERT INTO research_calls(id,epoch_id,job_id,generation,owner,request_key,
            request_hash,request_id,input_bound,output_bound,cost_bound,state)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
            (identity, epoch['id'], job['id'], job['generation'], actor['name'], key,
             fingerprint, stored['id'], input_token_bound, output_token_limit, cost_bound_units, 'reserved'))
        self._event(actor['name'], 'provider_call_reserved', call_id=identity, epoch_id=epoch['id'],
                    request_id=stored['id'], reservation=reservation)
        return {'call_id': identity, 'dispatch': True, 'state': 'reserved','deadline':deadline}

    def _inspect_research_epoch(self, actor, epoch_id):
        epoch = self._epoch(epoch_id)
        result = {**epoch, 'usage': self._call_usage(epoch_id), 'calls': self._calls_for(epoch_id)}
        if 'budget_overlay' in epoch['request']:
            from .epoch_budget_dispatch import inspect
            result['budget_overlay'] = inspect(self, epoch)
        if 'review_continuation' in epoch['request']:
            from .review_continuation import inspect
            result['review_continuation'] = inspect(self, epoch)
        return result

    def _revoke_research_epoch_budget(self, actor, epoch_id):
        from .epoch_budget_dispatch import revoke
        epoch = self._epoch(epoch_id)
        if 'review_continuation' in epoch['request']:
            from .review_continuation import revoke
            result = revoke(self, epoch)
            self._event(actor['name'], 'review_continuation_revoked', epoch_id=epoch_id)
            return result
        if 'budget_overlay' not in epoch['request']:
            raise Denied('This epoch has no optional resource authorization')
        result = revoke(self, epoch)
        self._event(actor['name'], 'research_epoch_budget_revoked', epoch_id=epoch_id)
        return result
