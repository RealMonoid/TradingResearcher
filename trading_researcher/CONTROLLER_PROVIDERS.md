# Controller-owned auxiliary provider calls

The optional direct-dispatch path closes a transport provenance gap: worker-submitted
responses, including scripted replies labeled `live`, cannot create a controller
invocation record. It does not certify the meaning or empirical truth of a response.

## Configuration and flow

The trusted local operator passes `provider_routes` when constructing `Broker`.
It maps the exact installed model name to `provider` (`openai` or `anthropic`),
`key_file`, `budget_file`, and the corresponding adapter `config`. The complete
configuration is copied. There is no RPC for replacing routes, supplying adapters,
changing destinations, or submitting a controller response. No route is enabled
by default. The existing adapter configuration, credentials, expiry and aggregate
spend ledger rules still apply. Reuse the approved ledger across runs; a new
registry is not a new spending authorization.

For a frozen auxiliary job, call `run_auxiliary_once(client)` without supplying a
worker-side provider. The worker RPC `invoke_auxiliary_provider(lease, key)` accepts
only the current lease and dispatch key. The controller derives the original exact
input packet, checks the live USD profile and adapter settings, reserves the
original epoch budget, and commits `provider-invocation-input/1` before launching
the installed adapter in the existing bounded child process. Integer currency
units remain one billion units per USD. No extra tools or model calls are added.

Network work holds no registry transaction or mutex. Heartbeats remain available;
cancelling the runner blocks its lease so the child is stopped. Terminating local
work cannot undo a request already accepted by the remote provider. Unknown usage
retains its reservation. The parent stores the returned response and the protected
`provider-invocation/1` result in one transaction. The adapter run identity derives
from the durable call identity, preserving aggregate ledger accounting.

A repeated key returns the owned record or its unresolved status without another
dispatch. A prior worker-owned call cannot acquire provenance retrospectively.
After a crash, an unresolved reservation requires reconciliation; restarting the
broker does not replay it or infer a successful response. Routes must be supplied
again at startup for new calls. Existing records remain in registry backups.

## Evidence and limits

Input records retain exact request identity, configuration, model, installed-source
fingerprints and host creation time. Results bind the input and response, receipt,
source-stability check and execution path. Times are Unix seconds in UTC; the
adapter usage ledger additionally records ISO UTC times, reported model identity,
known tokens and conservative currency bounds. Credential contents and credential
or ledger paths are not stored in invocation artifacts.

Late, over-budget, unknown-accounting, or source-drift results are retained but
returned as `unusable`, without a completed response payload. They cannot supply
formalization or semantic-review completion through the alternate record APIs.
Other provider failures remain explicit failed responses, never successful reviews.

The evidence means that the trusted controller selected an installed direct
adapter and retained its result. It is not remote cryptographic attestation, an OS
sandbox, proof of independent thought, or verification that a vendor's model alias
identifies immutable weights. The local operator, installed handlers and OS remain
trusted. Offline mocked transports test this boundary but do not establish real
API execution. Historical scripted records are unchanged.

`semantic-review-record/1` still reports actual independent model judgment as
`UNVERIFIED` and scientific readiness as false. A substantive real review, semantic
admission, scientific calibration and freeze remain separate work. See
[auxiliary research](AUXILIARY_RESEARCH.md) and the
[implementation verification](../docs/reviews/implementation-2026-10-25/controller-provider-verification.json).
