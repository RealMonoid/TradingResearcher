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


def demo(directory):
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise Invalid('Demo requires a new or empty directory')
    broker = Broker(directory)
    server = LocalServer(broker)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        admin = Client(server.url, broker.admin_token)
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
    for name in ('init', 'serve', 'verify', 'demo'):
        command = commands.add_parser(name)
        command.add_argument('--directory', required=True)
        if name == 'serve':
            command.add_argument('--port', type=int, default=8765)
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
    if args.command == 'demo':
        emit(demo(args.directory))
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
            emit(broker.call(broker.admin_token, 'verify'))
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
