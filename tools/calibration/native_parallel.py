"""Run the approved D100 inventory through the pinned host controller.

Use a separate fixed-source checkout. This command does not grant scientific
admission or protected-data access, and never resumes retired Scalar execution.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from trading_researcher.coordination import Broker
from trading_researcher.native_calibration_controller import NativeCalibrationController
from trading_researcher.study_process_control import PRIORITY_CLASS


def low_priority():
    if sys.platform != 'win32':
        raise RuntimeError('The approved native runtime requires its qualified Windows host')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.SetPriorityClass.restype = wintypes.BOOL
    kernel.GetPriorityClass.argtypes = [wintypes.HANDLE]
    kernel.GetPriorityClass.restype = wintypes.DWORD
    handle = kernel.GetCurrentProcess()
    if not kernel.SetPriorityClass(handle, PRIORITY_CLASS) or kernel.GetPriorityClass(handle) != PRIORITY_CLASS:
        raise RuntimeError('Native controller could not establish BELOW_NORMAL priority')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--run-directory', type=Path, required=True)
    parser.add_argument('--runtime-archive', type=Path, required=True)
    parser.add_argument('--runtime-manifest', type=Path, required=True)
    parser.add_argument('--predecessor-pool')
    parser.add_argument('--predecessor-checkpoint')
    parser.add_argument('--predecessor-terminal-receipt', type=Path)
    args = parser.parse_args()
    predecessor = (args.predecessor_pool, args.predecessor_checkpoint, args.predecessor_terminal_receipt)
    if any(value is not None for value in predecessor) and not all(value is not None for value in predecessor):
        parser.error('All three predecessor fields are required for the single pre-final source correction')
    correction = None if args.predecessor_pool is None else {
        'key': 'd100-native-source-correction', 'predecessor_pool_id': args.predecessor_pool,
        'expected_checkpoint': args.predecessor_checkpoint,
        'terminal_receipt_path': str(args.predecessor_terminal_receipt.resolve())}
    low_priority()
    with_broker = Broker(args.registry)
    primary_error = None
    try:
        controller = NativeCalibrationController(with_broker, args.run_directory, driver_file=Path(__file__))
        result = controller.run_all(with_broker.admin_token, archive_path=args.runtime_archive,
                                    manifest_path=args.runtime_manifest, correction_args=correction)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0 if result['status'] == 'COMPLETE_NUMERICAL_INVENTORY' else 2
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        try:
            with_broker.close()
        except BaseException as exc:
            if primary_error is None:
                raise
            primary_error.add_note('Controller Registry close failed: ' + type(exc).__name__)


if __name__ == '__main__':
    raise SystemExit(main())
