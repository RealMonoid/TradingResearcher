"""Durable, host-owned reservations for provider-neutral research calls.

This module contains no provider SDK or HTTP call. A trusted adapter must supply
conservative token/currency bounds. Unknown usage keeps the reservation charged;
an observed overrun halts the epoch rather than hiding the accounting failure.
"""
import uuid

from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied
from .context_views import SECTION_TOOL, PRESENTATION_PROFILES


PROFILE_FIELDS = {'model', 'prompt_version', 'max_calls', 'max_tokens', 'max_seconds',
                  'max_cost_units', 'currency', 'mode', 'prompts', 'tools', 'generation_parameters',
                  'max_output_tokens', 'call_timeout_seconds', 'max_retries'}
REQUEST_FIELDS = {'model', 'prompt_version', 'messages', 'tools', 'generation_parameters'}


class ResearchCalls:
    def _initialize_research_calls(self, existing):
        found = self._db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_call_meta'").fetchone()
        if found:
            version = self._db.execute('SELECT version FROM research_call_meta WHERE singleton=1').fetchone()
            if version is None or version[0] != 1:
                raise Invalid('Unsupported research-call schema')
            return
        if existing:
            self._preserve_schema_checkpoint('before-research-calls-v1.sqlite3')
        with self._transaction():
            self._db.execute('CREATE TABLE research_call_meta(singleton INTEGER PRIMARY KEY CHECK(singleton=1), version INTEGER NOT NULL)')
            self._db.execute('''CREATE TABLE research_epochs(id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
                request TEXT NOT NULL, created_at INTEGER NOT NULL, state TEXT NOT NULL)''')
            self._db.execute('''CREATE TABLE research_calls(id TEXT PRIMARY KEY,
                epoch_id TEXT NOT NULL REFERENCES research_epochs(id), job_id TEXT NOT NULL REFERENCES jobs(id),
                generation INTEGER NOT NULL, owner TEXT NOT NULL REFERENCES principals(name), request_key TEXT NOT NULL,
                request_hash TEXT NOT NULL, request_id TEXT NOT NULL REFERENCES artifacts(id),
                input_bound INTEGER NOT NULL, output_bound INTEGER NOT NULL, cost_bound INTEGER NOT NULL,
                response_id TEXT REFERENCES artifacts(id), charged_tokens INTEGER, charged_cost INTEGER,
                receipt TEXT, state TEXT NOT NULL,
                UNIQUE(job_id,generation,request_key))''')
            self._db.execute('INSERT INTO research_call_meta VALUES(1,1)')
            for table, fields in [('research_epochs', 'id,request_key,request,created_at'),
                                   ('research_calls', 'id,epoch_id,job_id,generation,owner,request_key,request_hash,request_id,input_bound,output_bound,cost_bound')]:
                self._db.execute(f'''CREATE TRIGGER immutable_{table}_identity BEFORE UPDATE OF {fields}
                    ON {table} BEGIN SELECT RAISE(ABORT,'immutable call identity'); END''')
                self._db.execute(f'''CREATE TRIGGER immutable_{table}_delete BEFORE DELETE ON {table}
                    BEGIN SELECT RAISE(ABORT,'retained call history'); END''')

    def _epoch(self, epoch_id):
        row = self._db.execute('SELECT * FROM research_epochs WHERE id=?', (epoch_id,)).fetchone()
        if row is None:
            raise Denied('Research epoch unavailable')
        return {**dict(row), 'request': decode(row['request'])}

    def _create_research_epoch(self, actor, key, context_id, workers, profile):
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
        for name, ceiling in [('max_calls', 12), ('max_tokens', 80000), ('max_seconds', 1800)]:
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
        request = {'context_id': context_id, 'workers': workers, 'profile': profile}
        old = self._db.execute('SELECT id,request FROM research_epochs WHERE request_key=?', (key,)).fetchone()
        if old:
            if old['request'] != canonical(request):
                raise Conflict('Epoch key already binds a different frozen request')
            return {'id': old['id']}
        identity = uuid.uuid4().hex
        self._db.execute('INSERT INTO research_epochs VALUES(?,?,?,?,?)',
                         (identity, key, canonical(request), self._now(), 'active'))
        self._event(actor['name'], 'research_epoch_created', epoch_id=identity, request=request)
        return {'id': identity}

    def _research_spec_check(self, spec):
        if 'research_epoch_id' not in spec:
            if set(spec)&{'research_call_profile','research_inputs'} or spec['kind']=='semantic-review/v1':
                raise Invalid('Auxiliary model work requires an original research epoch')
            return
        epoch = self._epoch(spec['research_epoch_id'])
        request = epoch['request']
        if spec['kind'] in ('formalization/v1','semantic-review/v1'):
            from .auxiliary import validate_profile
            validate_profile(spec.get('research_call_profile'),request['profile'])
            self._auxiliary_packet_for_spec(spec)
            return
        if set(spec)&{'research_call_profile','research_inputs'}:
            raise Invalid('Discovery profiles and snapshots cannot be overridden per job')
        if (spec['kind'] != 'research-record/v1' or spec['context_id'] != request['context_id']
                or len(spec['allowed_workers']) != 1
                or not set(spec['allowed_workers']) <= set(request['workers'])):
            raise Invalid('Research job must preserve the epoch snapshot and perspective')

    def _effective_research_profile(self,job):
        profile=decode(canonical(self._epoch(job['spec']['research_epoch_id'])['request']['profile']))
        if 'research_call_profile' in job['spec']:
            selected=job['spec']['research_call_profile']
            profile.update({k:v for k,v in selected.items() if k!='prompt'})
            profile['prompts']={job['spec']['allowed_workers'][0]:selected['prompt']}
            profile['tools']=[]
        elif 'perspective_profiles' in profile:
            profile.update(profile['perspective_profiles'][job['spec']['allowed_workers'][0]])
        return profile

    def _call_usage(self, epoch_id):
        row = self._db.execute('''SELECT COUNT(*),
            COALESCE(SUM(COALESCE(charged_tokens,input_bound+output_bound)),0),
            COALESCE(SUM(COALESCE(charged_cost,cost_bound)),0)
            FROM research_calls WHERE epoch_id=?''', (epoch_id,)).fetchone()
        return {'calls': row[0], 'tokens': row[1], 'cost_units': row[2]}

    def _research_completion_check(self, job):
        if 'research_epoch_id' not in job['spec']:
            return
        epoch=self._epoch(job['spec']['research_epoch_id'])
        if epoch['state']!='active' or self._now()>=epoch['created_at']+epoch['request']['profile']['max_seconds']:
            raise Denied('The original research epoch is halted or expired')
        if 'research_call_profile' in job['spec'] and self._db.execute(
                "SELECT 1 FROM research_calls WHERE epoch_id=? AND state='reserved'",(epoch['id'],)).fetchone():
            raise Denied('An unresolved epoch dispatch prevents auxiliary completion')
        if self._db.execute("SELECT 1 FROM research_calls WHERE job_id=? AND state='reserved'", (job['id'],)).fetchone():
            raise Denied('A research job cannot complete with an unresolved provider dispatch')

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
        self._db.execute('''INSERT INTO research_calls(id,epoch_id,job_id,generation,owner,request_key,
            request_hash,request_id,input_bound,output_bound,cost_bound,state)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
            (identity, epoch['id'], job['id'], job['generation'], actor['name'], key,
             fingerprint, stored['id'], input_token_bound, output_token_limit, cost_bound_units, 'reserved'))
        self._event(actor['name'], 'provider_call_reserved', call_id=identity, epoch_id=epoch['id'],
                    request_id=stored['id'], reservation=reservation)
        return {'call_id': identity, 'dispatch': True, 'state': 'reserved','deadline':deadline}

    def _finish_research_call(self, actor, lease, call_id, response, usage=None):
        if self._db.execute('SELECT 1 FROM provider_invocations WHERE call_id=?', (call_id,)).fetchone():
            raise Denied('Only the controller may settle its own provider dispatch')
        return self._settle_research_call(actor, lease, call_id, response, usage)

    def _settle_research_call(self, actor, lease, call_id, response, usage=None):
        if type(lease) is not dict or set(lease) != {'job_id', 'generation'}:
            raise Denied('Invalid call capability')
        call = self._db.execute('SELECT * FROM research_calls WHERE id=?', (call_id,)).fetchone()
        if (call is None or call['owner'] != actor['name'] or call['job_id'] != lease['job_id']
                or type(lease['generation']) is not int or call['generation'] != lease['generation']):
            raise Denied('Call unavailable to this capability')
        if type(response) is not dict:
            raise Invalid('Normalized provider response must be an object')
        accounting_valid = True
        if usage is not None:
            accounting_valid = (type(usage) is dict
                and set(usage) == {'input_tokens', 'output_tokens', 'cost_units'}
                and all(type(value) is int and value >= 0 for value in usage.values()))
        known_usage = usage if accounting_valid else None
        body = {'schema': 'provider-response/1', 'response': response, 'usage': usage, 'call_id': call_id}
        if call['state'] != 'reserved':
            if canonical(self._artifact(call['response_id'])['body']) != canonical(body):
                raise Conflict('Provider response is already recorded')
            return decode(call['receipt'])
        job = self._job(call['job_id'])
        epoch=self._epoch(call['epoch_id'])
        request_artifact = self._artifact(call['request_id'])
        deadline=request_artifact['body'].get('dispatch_deadline',epoch['created_at']+epoch['request']['profile']['max_seconds'])
        late = (job['generation'] != call['generation'] or job['owner'] != actor['name']
                or job['state'] != 'running' or job['lease_until'] <= self._now()
                or self._now()>=epoch['created_at']+epoch['request']['profile']['max_seconds'] or self._now()>=deadline)
        stored = self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
            'origin': 'controller', 'job_id': call['job_id'], 'generation': call['generation'],
            'exposed_to': actor['name'], 'context_id': request_artifact['context_id'],
            'data_class': 'work_product', 'body': body, 'source_refs': [call['request_id']],
            'exposure': sorted(set(request_artifact['exposure']) | {call['request_id']}),
            'authority': 'provider_report_not_scientific_evidence'})
        within = accounting_valid and (known_usage is None or (
            known_usage['input_tokens'] <= call['input_bound']
            and known_usage['output_tokens'] <= call['output_bound']
            and known_usage['cost_units'] <= call['cost_bound']))
        receipt = {'call_id': call_id, 'response_id': stored['id'], 'late': late,
                   'within_reservation': within, 'usage_unknown': known_usage is None,
                   'accounting_valid': accounting_valid}
        self._db.execute('''UPDATE research_calls SET response_id=?,charged_tokens=?,charged_cost=?,receipt=?,state=?
            WHERE id=?''', (stored['id'], None if known_usage is None else known_usage['input_tokens'] + known_usage['output_tokens'],
                            None if known_usage is None else known_usage['cost_units'], canonical(receipt),
                            'accounting_invalid' if not accounting_valid else ('recorded' if within else 'overrun'), call_id))
        if not within:
            self._db.execute("UPDATE research_epochs SET state='halted' WHERE id=?", (call['epoch_id'],))
        self._event(actor['name'], 'provider_response_recorded', **receipt)
        return receipt

    def _calls_for(self, epoch_id, job_id=None, generation=None):
        records = []
        for row in self._db.execute('SELECT * FROM research_calls WHERE epoch_id=? ORDER BY rowid', (epoch_id,)):
            if job_id is not None and (row['job_id'] != job_id or row['generation'] != generation):
                continue
            request = self._artifact(row['request_id'])['body']['request']
            reply = None if row['response_id'] is None else self._artifact(row['response_id'])['body']
            records.append({'id': row['id'], 'state': row['state'], 'request': request, 'reply': reply,
                            'usage_unknown': row['charged_tokens'] is None,
                            'job_id': row['job_id'], 'generation': row['generation']})
        return records

    def _research_call_state(self, actor, lease):
        job = self._owned(actor, lease)
        epoch = self._epoch(job['spec'].get('research_epoch_id'))
        return {'profile': self._effective_research_profile(job),
                'calls': self._calls_for(epoch['id'], job['id'], job['generation'])}

    def _inspect_research_epoch(self, actor, epoch_id):
        epoch = self._epoch(epoch_id)
        return {**epoch, 'usage': self._call_usage(epoch_id), 'calls': self._calls_for(epoch_id)}
