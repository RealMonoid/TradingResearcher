"""Run with python -B -m trading_researcher --help; standard library only."""
import argparse
import json
from pathlib import Path
import sys
import threading
import time

from .codec import decode, Invalid
from .coordination import Broker
from .server import Client, LocalServer
from .worker import run_once


def emit(value):
    print(json.dumps(value, indent=2, ensure_ascii=False), flush=True)


def demo(directory, research_memory=False, research_loop=False):
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise Invalid('Demo requires a new or empty directory')
    broker = Broker(directory)
    server = LocalServer(broker)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        admin = Client(server.url, broker.admin_token)
        if research_loop:
            from .research_demo import run_research_demo
            return run_research_demo(admin, server.url, directory)
        if research_memory:
            from .memory_demo import run_memory_demo
            return run_memory_demo(admin, server.url, directory)
        credential = admin.call('register_worker', name='calculator', role='executor', capabilities=['decimal-sum/v1'])
        source = admin.call('add_source', body={'values': ['0.1', '0.2', '-0.05'], 'fixture': True},
                            data_class='development', exposure=['synthetic-demo'])
        context = admin.call('create_context', role='executor', epoch=1, artifact_ids=[source['id']])
        spec = {'kind': 'decimal-sum/v1', 'context_id': context['id'], 'purpose': 'Synthetic infrastructure smoke test',
                'allowed_workers': ['calculator'], 'max_attempts': 2, 'lease_seconds': 10,
                'deadline': int(time.time()) + 60, 'dependencies': []}
        job = admin.call('enqueue', key='demo-sum', spec=spec)
        completion = run_once(Client(server.url, credential['token']))
        report = {'scope': 'Synthetic local coordination smoke test; no market evidence',
                  'completion': completion, 'job_id': job['id'], 'integrity': admin.call('verify'),
                  'directory': str(directory.resolve())}
        (directory / 'demo-result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        return report
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
        broker.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    calibration_command = commands.add_parser('assess-calibration-counts',
        help='Check adopted calibration count thresholds; no simulation, certificate or network')
    calibration_command.add_argument('--request', required=True, help='JSON file containing manifest and observations')
    usage_command = commands.add_parser('provider-usage', aliases=['openai-usage'], help='Read persisted inference token usage; no network or API key access')
    usage_command.add_argument('--ledger', required=True)
    for name in ('acquire-binance-month', 'inspect-binance-month'):
        command = commands.add_parser(name)
        command.add_argument('--directory', required=True, help='Owned acquisition directory, not a registry')
        if name == 'acquire-binance-month':
            command.add_argument('--symbol', required=True, choices=['BTCUSDT', 'ETHUSDT'])
            command.add_argument('--month', required=True, help='YYYY-MM in the adopted 2020-2025 profile')
    for name in ('init', 'serve', 'verify', 'certify-reference', 'revalidate-reference', 'certify-features',
                 'compile-hypothesis', 'execute-development',
                 'backup-bundle', 'restore-bundle', 'demo', 'memory-demo', 'research-demo',
                 'retain-binance-month', 'retain-binance-docs', 'normalize-binance-partition'):
        command = commands.add_parser(name)
        command.add_argument('--directory', required=True)
        if name == 'serve':
            command.add_argument('--port', type=int, default=8765)
        elif name == 'revalidate-reference':
            command.add_argument('--source-package-id', required=True)
        elif name == 'certify-features':
            command.add_argument('--data-snapshot-id', required=True)
        elif name == 'compile-hypothesis':
            command.add_argument('--formalization-id', required=True)
            command.add_argument('--feature-certificate-id', required=True)
            command.add_argument('--reference-certificate-id', required=True)
            command.add_argument('--as-of', required=True)
            command.add_argument('--max-steps', type=int, required=True)
        elif name == 'execute-development':
            command.add_argument('--compiled-id', required=True)
        elif name == 'backup-bundle':
            command.add_argument('--destination', required=True)
        elif name == 'restore-bundle':
            command.add_argument('--bundle', required=True)
            command.add_argument('--operator-key-file', required=True)
        elif name in ('retain-binance-month', 'retain-binance-docs'):
            command.add_argument('--source-directory', required=True, help='Existing exact acquisition directory')
        elif name == 'normalize-binance-partition':
            command.add_argument('--request', required=True, help='Explicit partition/source/scenario request JSON')
    for name in ('rpc', 'worker'):
        command = commands.add_parser(name)
        command.add_argument('--url', required=True)
        command.add_argument('--token-file', required=True)
        if name == 'rpc':
            command.add_argument('--request', required=True, help='JSON file containing op and args')
        else:
            command.add_argument('--max-jobs', type=int, default=1)
            command.add_argument('--idle-seconds', type=int, default=10)
    args = parser.parse_args()
    if args.command == 'assess-calibration-counts':
        from .binance_archive import _read_bounded
        from .calibration import assess_calibration
        from .codec import MAX_BYTES
        request = decode(_read_bounded(args.request, MAX_BYTES))
        if type(request) is not dict or set(request) != {'manifest', 'observations'}:
            raise Invalid('Calibration count request requires exactly manifest and observations')
        report = assess_calibration(**request)
        emit(report)
        if report['status'] != 'PASS_COUNTS_ONLY':
            raise SystemExit(2)
        return
    if args.command in ('provider-usage', 'openai-usage'):
        from .provider_usage import read_usage_report
        emit(read_usage_report(args.ledger))
        return
    if args.command in ('acquire-binance-month', 'inspect-binance-month'):
        from .binance_archive import acquire_month, read_acquisition
        if args.command == 'acquire-binance-month':
            emit(acquire_month(args.symbol, args.month, args.directory))
        else:
            emit(read_acquisition(args.directory)[0])
        return
    if args.command == 'restore-bundle':
        from .storage import restore_bundle
        emit(restore_bundle(args.bundle, args.directory, args.operator_key_file))
        return
    if args.command == 'normalize-binance-partition':
        from .binance_archive import _read_bounded
        from .binance_normalize import normalize_retained_partition
        from .codec import MAX_BYTES
        request = decode(_read_bounded(args.request, MAX_BYTES))
        if type(request) is not dict or set(request) != {'source_bundle_refs', 'provider_documents_ref',
                                                      'partition', 'universe', 'delay_seconds'}:
            raise Invalid('Normalization request must specify sources, documents, partition, universe and assumed delay')
        emit(normalize_retained_partition(args.directory, **request))
        return
    if args.command in ('demo', 'memory-demo', 'research-demo'):
        emit(demo(args.directory, research_memory=args.command == 'memory-demo',
                  research_loop=args.command == 'research-demo'))
        return
    if args.command in ('rpc', 'worker'):
        client = Client(args.url, Path(args.token_file).read_text(encoding='utf-8').strip())
        if args.command == 'rpc':
            request = decode(Path(args.request).read_bytes())
            if type(request) is not dict or set(request) != {'op', 'args'} or type(request['args']) is not dict:
                raise Invalid('Request file must contain op and args')
            emit(client.call(request['op'], **request['args']))
        else:
            if args.max_jobs < 1 or args.idle_seconds < 1:
                raise Invalid('Worker limits must be positive')
            completed, idle_until = 0, time.monotonic() + args.idle_seconds
            while completed < args.max_jobs and time.monotonic() < idle_until:
                result = run_once(client)
                if result is None:
                    time.sleep(0.2)
                else:
                    emit(result)
                    completed += 1
                    idle_until = time.monotonic() + args.idle_seconds
        return
    broker = Broker(args.directory)
    try:
        if args.command == 'init':
            emit({'directory': str(broker.directory), 'operator_key_file': str(broker.directory / 'operator.key')})
        elif args.command == 'verify':
            result = broker.call(broker.admin_token, 'verify')
            emit(result)
            if result['status'] != 'PASS':
                raise SystemExit(2)
        elif args.command in ('certify-reference', 'revalidate-reference'):
            operation = 'certify_reference' if args.command == 'certify-reference' else 'revalidate_reference'
            arguments = {} if args.command == 'certify-reference' else {'source_package_id': args.source_package_id}
            result = broker.call(broker.admin_token, operation, **arguments)
            emit(result)
            if result['body']['status'] != 'CERTIFIED':
                raise SystemExit(2)
        elif args.command == 'certify-features':
            result = broker.call(broker.admin_token, 'certify_features', data_snapshot_id=args.data_snapshot_id)
            emit(result)
            if result['body']['status'] != 'CERTIFIED':
                raise SystemExit(2)
        elif args.command in ('compile-hypothesis', 'execute-development'):
            if args.command == 'compile-hypothesis':
                result = broker.call(broker.admin_token, 'compile_hypothesis', formalization_id=args.formalization_id,
                    feature_certificate_id=args.feature_certificate_id, reference_certificate_id=args.reference_certificate_id,
                    as_of=args.as_of, max_steps=args.max_steps)
                expected = 'COMPILED'
            else:
                result = broker.call(broker.admin_token, 'execute_development', compiled_id=args.compiled_id)
                expected = 'DESCRIPTIVE_EXECUTION'
            emit(result)
            if result['body']['status'] != expected:
                raise SystemExit(2)
        elif args.command == 'backup-bundle':
            emit(broker.call(broker.admin_token, 'backup_bundle', destination=args.destination))
        elif args.command in ('retain-binance-month', 'retain-binance-docs'):
            from .binance_ingest import retain_acquisition, retain_provider_documents
            retain = retain_acquisition if args.command == 'retain-binance-month' else retain_provider_documents
            emit(retain(broker, broker.admin_token, args.source_directory))
        else:
            server = LocalServer(broker, args.port)
            emit({'url': server.url, 'directory': str(broker.directory), 'state': 'serving'})
            try:
                server.serve_forever(poll_interval=0.2)
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
    finally:
        broker.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        sys.exit(1)
