"""Genuine temporary native inputs; synthetic HTTP only, no market authority.

Normalization, retained blobs, feature/runtime certificates, frozen finite
slots, full packets, controller invocations and shared-ledger receipts are real
local code. Discovery and auxiliary outputs are fixed test doubles. A
software SATISFIED meaning-process result here is not actual LLM judgment.
There is no seeded feature metadata and no prequalified scientific record.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
from unittest.mock import patch

import inquiry_resource_support as finite_support
from trading_researcher.auxiliary import run_auxiliary_once
from trading_researcher.auxiliary_views import REUSE_SCOPE
from trading_researcher.binance_archive import capture_provider_docs
from trading_researcher.binance_ingest import retain_provider_documents
from trading_researcher.codec import digest
from trading_researcher.exact_execution import ExactExecutionBroker
from trading_researcher.exact_formalization import CONTRACT
from trading_researcher.meaning_reviews import PROMPT, PROTOCOL


CLOSE = 'BTCUSDT.close@binance-spot-15m-v1'
START = '2020-01-01T00:15:00Z'
END = '2020-01-01T01:00:00Z'
AS_OF = '2020-01-01T00:59:59Z'
ORIGINAL = (
    'Synthetic engineering original, not a market discovery: use only BTCUSDT on the exact 900-second grid '
    'in [2020-01-01T00:15:00Z,2020-01-01T01:00:00Z). Let C(s) denote the certified close at its exclusive '
    'complete-bar end s, with the explicitly assumed 900-second publication delay. Scope is true when '
    'C(t-900) is known and strictly positive; missing or unavailable scope input makes scope unknown, '
    'and nonpositive scope input makes scope false. Within that scope, the condition is '
    '(C(t-900)/(100 USDT/BTC)) squared strictly greater than one. This fixed ratio, exponent two and '
    'threshold one are declared test commitments, not selected from outcomes. '
    'The outcome is 10000*abs(ln(C(t)/C(t-900))) in absolute log basis points at anchor a=t+900; C(t) is '
    'an outcome-only input that becomes available at that anchor, not an executable entry price. '
    'Both endpoints must be finite, strictly positive, in this development partition and available by '
    'min(as_of,exclusive_end-1). Missing, unavailable or nonpositive required endpoints make the outcome '
    'missing. Preserve exact slots, no filling, early missing scope and end-boundary censoring. '
    'Compare the equal-row mean among condition-true observed outcomes with the whole scope-true observed '
    'mean; retain condition-unknown observed outcomes in the whole-scope denominator only. Direction is '
    'positive as a synthetic interface commitment, not a measured result. No weighting, nuisance fitting, '
    'cross-instrument input, policy, economic conclusion or scientific classification is requested.'
)


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': str(value)}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def lag(bars):
    return {'op': 'lag', 'arg': {'op': 'feature', 'ref': CLOSE}, 'bars': bars}


def paths(node, path):
    if node['op'] == 'literal':
        yield path + '/value'
    if node['op'] in ('lag', 'trailing_mean', 'trailing_median', 'trailing_product', 'trailing_all'):
        yield path + '/bars'
    if node['op'] == 'integer_power':
        yield path + '/exponent'
    for key in ('arg', 'left', 'right'):
        if key in node:
            yield from paths(node[key], path + '/' + key)


class ExactExecutionFixture:
    """Prepare genuine inputs and four synthetic native calls; no execution yet."""
    def __init__(self, *, run_roles=True):
        self.finite = None
        try:
            import binding_support
            import test_binance_normalize as normalization_tests
            original_binding_fixture = binding_support.BindingFixture
            original_setup = normalization_tests.NormalizeTests.setUp
            def setup_with_reviewed_documents(normalizer):
                original_setup(normalizer)
                # Preserve the old fixture and its initial placeholder history.
                # The actual normalization below receives the unchanged exact
                # already-reviewed public bytes through genuine ingestion.
                pinned = {
                    'README.md': '2e133d9945a9263a02781369078e72805eff074680f305cd5460016471c6caad',
                    'TERMS_AND_CONDITIONS.md': '99c4921dbe023cd68c1a447775707d621453cc78aec6ac0bfe2e6c06a5114ee0',
                }
                directory = Path(__file__).parent / 'fixtures' / 'paired_provider_documents'
                values = {name: (directory / (name + '.source')).read_bytes() for name in pinned}
                if {name: hashlib.sha256(raw).hexdigest() for name, raw in values.items()} != pinned:
                    raise AssertionError('The committed reviewed provider-document bytes differ')
                captured = normalizer.root / 'exact-reviewed-provider-documents'
                capture_provider_docs(captured,
                    downloader=lambda url, limit: (values[url.rsplit('/', 1)[-1]], {}))
                normalizer.docs = retain_provider_documents(normalizer.broker, normalizer.token, captured)['id']
            # The new broker must exist BEFORE normalization/certification and
            # epoch binding. Never reopen/rebind an already frozen epoch.
            with patch.object(finite_support, 'FiniteInquiryBroker', ExactExecutionBroker), patch.object(
                    normalization_tests.NormalizeTests, 'setUp', setup_with_reviewed_documents), patch.object(
                    binding_support, 'BindingFixture', side_effect=lambda: original_binding_fixture(
                        case={'change': {'delay_seconds': 900}})):
                # The legacy binding fixture's baseline delay is zero. Supply
                # this original's explicit 900-second assumption as actual
                # normalization input before any certificate or frozen epoch.
                # Retain the partially constructed fixture too, so an ordinary
                # fail-closed admission error cannot orphan its open registry.
                self.finite = finite_support.Fixture.__new__(finite_support.Fixture)
                finite_support.Fixture.__init__(self.finite, full=True, create=False)
            f = self.finite
            self.broker, self.token = f.broker, f.token
            self.root, self.ledger = f.root, f.ledger
            self.snapshot, self.feature = f.base.snapshot, f.base.feature
            self.runtime = self.broker.certify_exact_runtime(self.token)
            if self.runtime['body']['status'] != 'CERTIFIED':
                raise AssertionError(self.runtime['body'])
            self.op('release_feature_evidence', certificate_id=self.feature['id'], target_epoch=2)
            for kind, role in f.role_profiles.items():
                role['profile']['generation_parameters']['openai_responses']['bounded_math_scope'] = REUSE_SCOPE
                if kind == 'formalization/v1':
                    role['profile']['prompt_version'] = 'synthetic-exact-native-formalizer/1'
            review = f.role_profiles['semantic-review/v1']['profile']
            if (review['prompt_version'], review['prompt']) != (PROTOCOL, PROMPT):
                raise AssertionError('The substantive independent reviewer was changed')
            f.policy = self.broker.prepare_resource_disposition(self.token,
                role_profiles=f.role_profiles, discovery_run_ids={'first': 'synthetic-first', 'second': 'synthetic-second'})
            # This fixture field feeds only the fixed synthetic discovery reply;
            # no committed original artifact is rewritten.
            f.base.base['original_idea_text'] = ORIGINAL
            f.create_epoch()
            self.discovery = f.discover()
            self.idea, self.epoch = f.idea, f.epoch
            self.catalog_id = self.snapshot['body']['catalog_id']
            self.catalog = self.op('get_artifact', artifact_id=self.catalog_id)['body']['features']
            self.definition_ids = [self.feature['body']['definitions_id']]
            self.candidate = self.make_candidate()
            self.mapping = {'status': 'equivalent', 'segments': [
                {'text': ORIGINAL, 'path': '/condition_ast',
                 'interpretation': 'Fixed engineering formula assertion only; actual model semantics remain unverified.'}],
                'differences': []}
            if run_roles:
                self.formalize()
                self.review()
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.finite is not None:
            fixture = self.finite
            self.finite = None
            try:
                if getattr(fixture, 'base', None) is not None:
                    fixture.base.close()
                elif getattr(fixture, 'broker', None) is not None:
                    fixture.broker.close()
            finally:
                if getattr(fixture, 'temp', None) is not None:
                    fixture.temp.cleanup()

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def make_candidate(self):
        def program(expression):
            return {'schema': 'research-ast/4', 'catalog_hash': digest(self.catalog), 'expression': expression}
        scope = binary('gt', lag(1), literal(0, 'USDT/BTC'))
        condition = binary('gt', {'op': 'integer_power', 'arg': binary('div', lag(1), literal(100, 'USDT/BTC')),
                                  'exponent': 2}, literal(1))
        logarithm = {'op': 'ln', 'arg': binary('div', lag(1), lag(2))}
        absolute = {'op': 'abs', 'arg': logarithm}
        # Exact zero-valued positive-domain guards use no extra raw inputs.
        for endpoint in (lag(1), lag(2)):
            absolute = binary('add', absolute, binary('mul', literal(0),
                {'op': 'ln', 'arg': binary('div', endpoint, literal(1, 'USDT/BTC'))}))
        outcome = binary('mul', literal(10000, 'basis_points'), absolute)
        value = {'schema': 'hypothesis-exec/3', 'idea_ref': self.idea, 'claim_kind': 'difference',
            'scope_ast': program(scope), 'condition_ast': program(condition),
            'outcome': {'program': program(outcome), 'scale': 'quantity'},
            'comparator': {'kind': 'whole_scope'}, 'horizons': {'grid_seconds': 900, 'outcome_bars': 1},
            'test_universe': {'instruments': ['BTCUSDT'], 'start': START, 'end': END,
                              'data_snapshot_ref': self.snapshot['id']},
            'estimand': {'kind': 'conditional-minus-scope-mean/1', 'unit': 'basis_points', 'weighting': 'equal_rows',
                'missingness': 'scope-true-outcome-observed/1',
                'condition_unknown': 'exclude-from-condition-retain-in-scope', 'nuisance_fit': 'none', 'direction': 'positive'},
            'feature_refs': [CLOSE], 'parameter_origins': []}
        declared = ['/horizons/outcome_bars']
        for path, expression in (('/scope_ast/expression', scope), ('/condition_ast/expression', condition),
                                 ('/outcome/program/expression', outcome)):
            declared.extend(paths(expression, path))
        value['parameter_origins'] = [{'path': path, 'basis': 'preexisting_specification', 'source_refs': [self.idea],
            'rationale': 'Fixed synthetic original or exact domain/scale identity; no empirical fitting.'} for path in declared]
        return value

    def spec(self, kind):
        formal = kind == 'formalization/v1'
        f = self.finite
        refs = [self.idea, self.catalog_id, self.snapshot['id'], self.feature['id'], *self.definition_ids]
        inputs = {'definition_ids': list(self.definition_ids), 'feature_certificate_id': self.feature['id'],
                  'expression_contract': CONTRACT, 'reporting_contract': 'case-diagnostics/2'}
        if formal:
            inputs.update(idea_id=self.idea, catalog_id=self.catalog_id)
        else:
            refs.append(self.formalization['id'])
            inputs['formalization_id'] = self.formalization['id']
        context = self.op('create_context', role='formalizer', epoch=2 if formal else 3, artifact_ids=sorted(set(refs)))['id']
        epoch = self.op('inspect_research_epoch', epoch_id=self.epoch)
        worker = 'formal' if formal else 'review'
        return {'kind': kind, 'context_id': context, 'purpose': 'Genuine synthetic exact native gate qualification.',
                'allowed_workers': [worker], 'max_attempts': 1, 'lease_seconds': 600,
                'deadline': epoch['created_at'] + 1800, 'dependencies': [], 'research_epoch_id': self.epoch,
                'research_call_profile': deepcopy(f.role_profiles[kind]['profile']), 'research_inputs': inputs}

    def dispatch(self, kind, output):
        spec = self.spec(kind)
        worker = 'formal' if kind == 'formalization/v1' else 'review'
        job = self.op('enqueue', key='exact-fixture-' + worker, spec=spec)['id']
        post, calls = finite_support.fake_post(output)
        with patch('trading_researcher.openai_provider._post', side_effect=post), patch(
                'trading_researcher.inquiry.dispatch._invoke', side_effect=lambda p, r, o, t, c: p.complete(r, o, t)):
            result = run_auxiliary_once(self.finite.clients[worker], None)
        if not result.get('accepted'):
            raise AssertionError({'stage': kind, 'result': result})
        return self.op('get_artifact', artifact_id=result['artifact_id']), spec, job, calls

    def formalize(self):
        self.formalization, self.formal_spec, self.formal_job, self.formal_http = self.dispatch(
            'formalization/v1', {'status': 'final', 'candidate': self.candidate, 'semantic_report': self.mapping})
        body = self.formalization['body']
        if body['assessment']['status'] != 'STRUCTURE_CHECKED' or body['original_idea']['content']['text'] != ORIGINAL:
            raise AssertionError(body)
        batch = self.op('inspect', job_id=self.formal_job)['batch_id']
        self.op('release_batch', batch_id=batch, target_epoch=3)
        self.early_meaning = self.op('assess_meaning_review', key='exact-before-review', formalization_id=self.formalization['id'])
        return self.formalization

    def review(self, judgment='faithful'):
        review = {'judgment': judgment,
            'reason': 'Explicit synthetic HTTP response for this fixed engineering original; not actual LLM judgment.',
            'added_assumptions': [], 'omitted_assumptions': [], 'conflicts': [],
            'unresolved_meaning': [] if judgment == 'faithful' else ['Controlled synthetic uncertainty.'],
            'mapping_checks': [{'segment': index, 'judgment': judgment,
                'reason': 'Fixed scripted comparison response; no claim about real model behavior.'}
                for index in range(len(self.mapping['segments']))]}
        self.review_record, self.review_spec, self.review_job, self.review_http = self.dispatch(
            'semantic-review/v1', {'status': 'final', 'review': review})
        self.meaning = self.op('assess_meaning_review', key='exact-after-review', formalization_id=self.formalization['id'])
        self.meaning_status = self.op('inspect_meaning_review', assessment_id=self.meaning['id'])
        if judgment == 'faithful' and self.meaning_status['independent_semantic_review'] != 'SATISFIED':
            raise AssertionError(self.meaning_status)
        return self.meaning

    def compile(self, max_steps=100_000):
        return self.broker.compile_exact(self.token, formalization_id=self.formalization['id'],
            feature_certificate_id=self.feature['id'], as_of=AS_OF, max_steps=max_steps)

    def composition(self, compiled_id):
        return self.broker.certify_exact_composition(self.token, compiled_id=compiled_id)

    def execute(self, compiled_id, composition_id, meaning_assessment_id=None):
        return self.broker.execute_exact(self.token, compiled_id=compiled_id,
            meaning_assessment_id=self.meaning['id'] if meaning_assessment_id is None else meaning_assessment_id,
            composition_id=composition_id)
