"""Trusted worker wrapper; handlers receive frozen input records only.

The built-in handlers perform no model calls, shell commands, network retrieval,
or scientific evaluation. Future model adapters belong behind this boundary.
"""
import threading

from .checks import decimal_sum, source_report

HANDLERS = {'decimal-sum/v1': decimal_sum, 'source-report/v1': source_report}


def run_once(client, handlers=None):
    handlers = HANDLERS if handlers is None else handlers
    claimed = client.call('claim')
    if claimed is None:
        return None
    lease = claimed['lease']
    stopped = threading.Event()
    lost = threading.Event()

    def heartbeat():
        while not stopped.wait(max(0.05, claimed['spec']['lease_seconds'] / 3)):
            try:
                client.call('heartbeat', lease=lease)
            except Exception:
                lost.set()
                return

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        kind = claimed['spec']['kind']
        handler = handlers.get(kind)
        if handler is None:
            return client.call('block', lease=lease, reason='No installed worker handler',
                               needs=[kind], retry_when='A trusted compatible handler is installed')
        sources = [client.call('read_artifact', lease=lease, artifact_id=ref)
                   for ref in claimed['context']['artifact_ids']]
        try:
            body = handler(sources)
        except Exception as exc:
            return client.call('block', lease=lease, reason='Handler failed: ' + type(exc).__name__,
                               needs=['handler investigation'], retry_when='The diagnosed handler failure is resolved')
        if lost.is_set():
            return {'state': 'lease_lost', 'accepted': False}
        artifact = client.call('put_artifact', lease=lease, body=body,
                               source_refs=claimed['context']['artifact_ids'])
        return client.call('submit', lease=lease, artifact_id=artifact['id'])
    finally:
        stopped.set()
        thread.join(client.timeout + 1)
