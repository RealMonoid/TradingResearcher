"""Opt-in AST4 data-use integration of the existing controlled feedback imports."""
import hashlib
from pathlib import Path

from .binding import require
from .exact_execution import ExactExecutionBroker
from .feedback.breakout import BreakoutFeedbackBroker

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'exact-controlled-feedback/1'
SCHEMA = 'exact-development-data-use/2'
FILES = ('trading_researcher/exact_feedback.py', 'trading_researcher/EXACT_FEEDBACK.md',
         'trading_researcher/feedback/breakout.py')
LOADED = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}


class ExactFeedbackBroker(ExactExecutionBroker, BreakoutFeedbackBroker):
    """New entry point; frozen old brokers, profiles and results stay unchanged."""

    def _exact_feedback_sources(self):
        current = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
        require(current == LOADED, 'Exact feedback sources changed; restart and independently requalify')
        return current

    def _execution_sources(self):
        current = self._exact_feedback_sources()
        return {**super()._execution_sources(), **current}

    def _exact_source_identity(self):
        current = self._exact_feedback_sources()
        return {**super()._exact_source_identity(), **current}

    def _exact_data_use(self, dependencies):
        sources = self._execution_sources()
        target = dependencies['formalization']
        context = self._context(target['context_id'])
        # Check every inherited release even if a later data-use gap prevents
        # compilation. The existing import methods retain eligibility, typed
        # ownership, source/environment and dependency-usability checks.
        self._check_feedback_context(context)
        result = BreakoutFeedbackBroker._paired_data_use(self, dependencies)
        return {**result, 'schema': SCHEMA, 'controlled_feedback': {
            'profile': PROFILE, 'context_id': context['id'],
            'installed_sources': sources, 'scientific_readiness': False}}
