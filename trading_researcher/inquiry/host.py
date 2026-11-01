"""Opt-in inquiry presentation broker; legacy brokers and grants stay unchanged."""
import uuid

from ..codec import Invalid, canonical, decode, digest, integer, strings, text
from ..errors import Conflict, Denied
from ..research_calls import PROFILE_FIELDS, REQUEST_FIELDS
from ..paired_breakout.research import BreakoutResearchBroker
from ..feedback.reference_views import source_view
from . import presentation
from .profiles import OWNER, VERSION, verify_profile

BINDING_SCHEMA = 'inquiry-runtime-binding/1'


class InquiryBroker(BreakoutResearchBroker):
    """Separate operator entry point, retaining inherited access/accounting."""

    def _breakout_research_sources(self):
        return {**super()._breakout_research_sources(), **presentation.current_sources()}

    def prepare_inquiry_binding(self, token, *, base_profile, bundle):
        with self._mutex:
            self._binding_owner(token)
            verify_profile(bundle, base_profile, (presentation.ROOT / OWNER).read_bytes())
            binding = {'schema': BINDING_SCHEMA, 'base_profile': base_profile,
                       'profile_manifest': bundle['manifest'],
                       'installed_sources': self._breakout_research_sources()}
            self._validate_inquiry_profile(bundle['profile'], binding)
            return decode(canonical(binding))

    def _validate_inquiry_profile(self, profile, binding):
        if (type(binding) is not dict or set(binding) != {
                'schema', 'base_profile', 'profile_manifest', 'installed_sources'}
                or binding['schema'] != BINDING_SCHEMA):
            raise Invalid('Explicit exact inquiry runtime binding required')
        verify_profile({'profile': profile, 'manifest': binding['profile_manifest']},
                       binding['base_profile'], (presentation.ROOT / OWNER).read_bytes())
        if (profile.get('source_presentation') != presentation.SCHEMA
                or profile['prompt_version'] != VERSION
                or canonical(profile['tools']) != canonical(presentation.TOOLS)):
            raise Invalid('The new broker admits only the exact inquiry presentation and tools')
        if canonical(binding['installed_sources']) != canonical(self._breakout_research_sources()):
            raise Denied('Inquiry binding differs from the installed qualified source closure')

    def _inquiry_epoch_current(self, epoch):
        binding = epoch['request'].get('inquiry_binding')
        self._validate_inquiry_profile(epoch['request']['profile'], binding)
        return binding

    def _research_spec_check(self, spec):
        super()._research_spec_check(spec)
        if 'research_epoch_id' in spec:
            self._inquiry_epoch_current(self._epoch(spec['research_epoch_id']))

    def _research_call_state(self, actor, lease):
        state = super()._research_call_state(actor, lease)
        job = self._owned(actor, lease)
        binding = self._inquiry_epoch_current(self._epoch(job['spec']['research_epoch_id']))
        return {**state, 'inquiry_runtime': {
            'schema': BINDING_SCHEMA, 'installed_sources': binding['installed_sources']}}

    def _read_artifact(self, actor, lease, artifact_id):
        job = self._owned(actor, lease)
        if 'research_epoch_id' in job['spec']:
            self._inquiry_epoch_current(self._epoch(job['spec']['research_epoch_id']))
        return super()._read_artifact(actor, lease, artifact_id)

    def _search_memory(self, actor, lease, view='journal', query='', scope=None,
                       kind=None, after=0, limit=20):
        job = self._owned(actor, lease)
        if 'research_epoch_id' in job['spec']:
            self._inquiry_epoch_current(self._epoch(job['spec']['research_epoch_id']))
        return super()._search_memory(actor, lease, view, query, scope, kind, after, limit)

    def _auxiliary_input(self, actor, lease):
        job = self._owned(actor, lease)
        if 'research_epoch_id' in job['spec']:
            self._inquiry_epoch_current(self._epoch(job['spec']['research_epoch_id']))
        return super()._auxiliary_input(actor, lease)

    def _measure_development_external(self, token, args):
        with self._mutex:
            actor = self._principal(token)
            job = self._owned(actor, args.get('lease'))
            if 'research_epoch_id' in job['spec']:
                self._inquiry_epoch_current(self._epoch(job['spec']['research_epoch_id']))
        return super()._measure_development_external(token, args)

    def _initial_inquiry_messages(self, actor, lease, job, profile):
        context = self._context(job['spec']['context_id'])
        sources = [self._read_artifact(actor, lease, identity)
                   for identity in context['artifact_ids']]
        return presentation.initial_messages(profile, actor['name'], job['spec']['purpose'], sources)

    def _tool_artifacts(self, job, call_id, schema):
        rows = self._db.execute(
            "SELECT id,envelope FROM artifacts WHERE json_extract(envelope,'$.job_id')=? "
            "AND json_extract(envelope,'$.generation')=? "
            "AND json_extract(envelope,'$.body.schema')=? ORDER BY rowid",
            (job['id'], job['generation'], schema)).fetchall()
        return [dict(id=row['id'], **decode(row['envelope'])) for row in rows
                if decode(row['envelope'])['body'].get('call_id') == call_id
                or (schema == 'provider-tool-view/1'
                    and decode(row['envelope'])['body'].get('source_tool_result_id') == call_id)]

    def _expected_inquiry_messages(self, actor, lease, job, profile):
        initial = self._initial_inquiry_messages(actor, lease, job, profile)
        calls = self._calls_for(job['spec']['research_epoch_id'], job['id'], job['generation'])
        if not calls:
            return initial
        prior = calls[-1]
        if prior['reply'] is None:
            raise Denied('The prior dispatch remains unresolved')
        previous = prior['request']['messages']
        if canonical(previous[:3]) != canonical(initial):
            raise Denied('The retained inquiry packet differs from its exact bound sources')
        response = prior['reply']['response']
        output = response.get('output')
        status = output.get('status') if response.get('status') == 'completed' and type(output) is dict else response.get('status')
        expected = [*previous, {'role': 'assistant', 'content': canonical(response)}]
        if status in ('failed', 'timeout'):
            failures = sum(item['reply'] is not None and item['reply']['response'].get('status')
                           in ('failed', 'timeout') for item in calls)
            if failures > profile['max_retries']:
                raise Denied('Inquiry transport retries exceed the frozen allowance')
            return expected
        if status != 'tools' or type(output) is not dict:
            raise Denied('A terminal or malformed response permits no successor call')
        tools = output.get('calls')
        if (type(tools) is not list or not 1 <= len(tools) <= 16
                or any(type(tool) is not dict or type(tool.get('id')) is not str for tool in tools)
                or len({tool['id'] for tool in tools}) != len(tools)):
            raise Invalid('The retained tool batch is malformed')
        records = self._tool_artifacts(job, prior['id'], 'provider-tool-result/1')
        if len(records) != len(tools):
            raise Denied('Complete exact retained tool results are required before continuation')
        for tool, record in zip(tools, records, strict=True):
            body = record['body']
            if canonical(body.get('tool_request')) != canonical(tool):
                raise Denied('Tool result order or request differs from the provider response')
            visible = body
            if body['result'].get('status') == 'ok' and tool.get('name') == 'measure_development':
                visible = {**body, 'result': {'status': 'ok', 'value': source_view(body['result']['value'])}}
                views = self._tool_artifacts(job, record['id'], 'provider-tool-view/1')
                required = {'schema': 'provider-tool-view/1', 'presentation_profile': presentation.SCHEMA,
                            'source_tool_result_id': record['id'], 'model_visible_body': visible}
                if len(views) != 1 or canonical(views[0]['body']) != canonical(required):
                    raise Denied('Exact retained model-visible tool view is required')
            expected.append({'role': 'tool', 'content': canonical(visible)})
        return expected

    def _reserve_research_call(self, actor, lease, key, request, input_token_bound,
                               output_token_limit, cost_bound_units):
        job = self._owned(actor, lease)
        if 'research_epoch_id' not in job['spec']:
            raise Denied('This job has no inquiry research epoch')
        self._inquiry_epoch_current(self._epoch(job['spec']['research_epoch_id']))
        if job['spec']['kind'] == 'research-record/v1':
            prior = self._db.execute(
                'SELECT id FROM research_calls WHERE job_id=? AND generation=? AND request_key=?',
                (job['id'], job['generation'], key)).fetchone()
            if prior is None:
                expected = self._expected_inquiry_messages(actor, lease, job, self._effective_research_profile(job))
                if type(request) is not dict or canonical(request.get('messages')) != canonical(expected):
                    raise Invalid('Inquiry messages differ from the complete bound packet and retained trajectory')
        return super()._reserve_research_call(actor, lease, key, request, input_token_bound,
                                             output_token_limit, cost_bound_units)

    def _settle_research_call(self, actor, lease, call_id, response, usage=None):
        row = self._db.execute('SELECT epoch_id,state FROM research_calls WHERE id=?', (call_id,)).fetchone()
        # Authenticate and retain the response/accounting before any source-currentness denial.
        receipt = super()._settle_research_call(actor, lease, call_id, response, usage)
        epoch = self._epoch(row['epoch_id'])
        if row['state'] != 'reserved' or 'inquiry_binding' not in epoch['request']:
            return receipt
        try:
            self._inquiry_epoch_current(epoch)
            current = True
        except (OSError, Invalid, Denied):
            current = False
        receipt = {**receipt, 'installed_sources_unchanged': current}
        self._db.execute('UPDATE research_calls SET receipt=? WHERE id=?', (canonical(receipt), call_id))
        if not current:
            self._db.execute("UPDATE research_epochs SET state='halted' WHERE id=?", (row['epoch_id'],))
        self._event('controller', 'inquiry_source_check_after_response', call_id=call_id,
                    response_id=receipt['response_id'], installed_sources_unchanged=current)
        return receipt

    def _research_completion_check(self, job):
        if 'research_epoch_id' in job['spec']:
            self._inquiry_epoch_current(self._epoch(job['spec']['research_epoch_id']))
        return super()._research_completion_check(job)

    def _inquiry_resource_ceiling(self, context, workers, profile, disposition):
        if disposition is not None:
            raise Denied('A finite disposition requires its separate operator entry point')
        return 80000

    def _inquiry_resource_claim(self, epoch):
        pass

    def _inquiry_resource_existing(self, epoch):
        pass

    # Static fork of research_calls.py:6284dca04ccbdb47fd14df418aee5d2a78bf634b5174b41fbc94f90281ccf512
    def _create_research_epoch(self, actor, key, context_id, workers, profile, budget_overlay=None, review_continuation=None, inquiry_binding=None, resource_disposition=None):
        if budget_overlay is not None or review_continuation is not None:
            raise Denied('The inquiry route cannot reuse legacy grants or change the ordinary epoch cap')
        self._validate_inquiry_profile(profile, inquiry_binding)
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
        if type(profile) is not dict or not PROFILE_FIELDS <= set(profile) or set(profile) - PROFILE_FIELDS - optional_fields:
            raise Invalid('Missing or unexpected epoch profile fields')
        if type(profile['prompts']) is not dict or set(profile['prompts']) != set(workers):
            raise Invalid('Each perspective needs an explicit frozen prompt')
        for prompt in profile['prompts'].values():
            text(prompt, 'perspective prompt')
        if type(profile['tools']) is not list or type(profile['generation_parameters']) is not dict:
            raise Invalid('Tool definitions and generation parameters must be explicit')
        token_ceiling = self._inquiry_resource_ceiling(context, workers, profile, resource_disposition)
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
            from ..auxiliary import PROFILE_FIELDS as ROLE_FIELDS, validate_profile
            selected = profile['perspective_profiles']
            if type(selected) is not dict or set(selected) != set(workers):
                raise Invalid('Each perspective requires an explicit frozen call profile')
            for worker, settings in selected.items():
                if type(settings) is not dict or set(settings) != ROLE_FIELDS - {'prompt'}:
                    raise Invalid('Perspective call profile has missing or unexpected fields')
                validate_profile({**settings, 'prompt': profile['prompts'][worker]}, profile)
        request = {'context_id': context_id, 'workers': workers, 'profile': profile, 'inquiry_binding': inquiry_binding}
        if resource_disposition is not None:
            request['resource_disposition'] = resource_disposition
        old = self._db.execute('SELECT id,request FROM research_epochs WHERE request_key=?', (key,)).fetchone()
        if old:
            if old['request'] != canonical(request):
                raise Conflict('Epoch key already binds a different frozen request')
            self._inquiry_resource_existing(self._epoch(old['id']))
            return {'id': old['id']}
        identity = uuid.uuid4().hex
        created_at = self._now()
        self._db.execute('INSERT INTO research_epochs VALUES(?,?,?,?,?)', (identity, key, canonical(request), created_at, 'active'))
        self._inquiry_resource_claim(self._epoch(identity))
        self._event(actor['name'], 'research_epoch_created', epoch_id=identity, request=request)
        return {'id': identity}
