"""Explicit policy routing; legacy grant implementation remains byte-identical."""
from . import epoch_budget as legacy, complete_feedback_budget as complete, paired_budget as paired
from . import paired_correction_budget as correction
from .codec import Invalid


def _policy(policy):
    if policy == legacy.POLICY:
        return legacy
    if policy == complete.POLICY:
        return complete
    if policy == paired.POLICY:
        return paired
    if policy == correction.POLICY:
        return correction
    raise Invalid('Unknown research epoch budget overlay')


def validate(host, context, profile, policy):
    return _policy(policy).validate(host, context, profile, policy)


def claim(host, epoch):
    return _policy(epoch['request']['budget_overlay']).claim(host, epoch)


def inspect(host, epoch):
    return _policy(epoch['request']['budget_overlay']).inspect(host, epoch)


def reserve(host, epoch, job, identity, input_bound, output_bound, cost, *, request):
    module = _policy(epoch['request']['budget_overlay'])
    args = (host, epoch, job, identity, input_bound, output_bound, cost)
    return module.reserve(*args, request=request) if module in (complete, paired, correction) else module.reserve(*args)


def revoke(host, epoch):
    return _policy(epoch['request']['budget_overlay']).revoke(host, epoch)
