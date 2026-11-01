"""Explicit optional routing; every existing policy delegates unchanged."""
from .. import epoch_budget_dispatch as legacy
from . import budget

def validate(host, context, profile, policy):
    return (budget if policy == budget.POLICY else legacy).validate(host, context, profile, policy)

def _module(epoch):
    return budget if epoch['request']['budget_overlay'] == budget.POLICY else legacy

def claim(host, epoch): return _module(epoch).claim(host, epoch)
def inspect(host, epoch): return _module(epoch).inspect(host, epoch)
def revoke(host, epoch): return _module(epoch).revoke(host, epoch)

def reserve(host, epoch, job, identity, input_bound, output_bound, cost, *, request):
    return _module(epoch).reserve(host, epoch, job, identity, input_bound, output_bound, cost, request=request)
