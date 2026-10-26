"""Host-owned operational checks. These never assign scientific evidence status."""
from decimal import Decimal, localcontext
from fractions import Fraction
import re

from .codec import Invalid, text, canonical
from .memory import validate_record
from .formalization import validate_record as validate_formalization
from .auxiliary import validate_review_record

DECIMAL = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z')
VERSIONS = {'draft/v1', 'source-report/v1', 'decimal-sum/v1', 'research-record/v1', 'formalization/v1','semantic-review/v1'}


def decimal_sum(sources):
    """Small reference calculation, cross-checked by exact rational arithmetic."""
    values = []
    for source in sources:
        body = source['body']
        if not isinstance(body, dict) or type(body.get('values')) is not list:
            raise Invalid('Every input must contain a values list')
        values.extend(body['values'])
    if not values or len(values) > 1000:
        raise Invalid('The sum requires 1 through 1000 values')
    if any(type(v) is not str or len(v) > 100 or not DECIMAL.fullmatch(v) for v in values):
        raise Invalid('Use finite plain decimal strings with at most 100 characters')
    with localcontext() as context:
        context.prec = 256
        total = sum((Decimal(v) for v in values), Decimal(0))
        exact = sum((Fraction(v) for v in values), Fraction(0))
        if Fraction(total) != exact:
            raise Invalid('Independent rational check disagrees')
        return {'total': format(total, 'f'), 'count': len(values)}


def source_report(sources):
    """Copy records exactly; no unsupported numerical or scientific synthesis."""
    return {'records': [{'source_id': s['id'], 'body': s['body']} for s in sources]}


def validate(kind, result, sources):
    if kind=='semantic-review/v1':
        validate_review_record(result,sources)
        return 'Review input/response binding checked; actual independent model judgment and scientific readiness remain unverified'
    if kind == 'formalization/v1':
        validate_formalization(result, sources)
        return 'Formalization retention and structure checked; no semantic/scientific certificate issued'
    if kind == 'research-record/v1':
        validate_record(result)
        return 'Research record structure checked; claims and interpretations remain unverified'
    if kind == 'draft/v1':
        if type(result) is not dict or set(result) != {'finding', 'interpretation', 'uncertainty', 'next_action'}:
            raise Invalid('A draft needs finding, interpretation, uncertainty and next_action')
        for key, value in result.items():
            text(value, key)
        return 'Draft structure checked; claims remain unverified'
    if kind == 'source-report/v1':
        if canonical(result) != canonical(source_report(sources)):
            raise Invalid('Report must reproduce exactly the supplied source records')
        return 'Exact source fidelity checked; source truth is not certified'
    if kind == 'decimal-sum/v1':
        if canonical(result) != canonical(decimal_sum(sources)):
            raise Invalid('Calculation does not match the independent reference result')
        return 'Decimal calculation and independent rational check agree'
    raise Invalid('No trusted completion check is registered for this task kind')
