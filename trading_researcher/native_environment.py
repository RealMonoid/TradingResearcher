"""Selected native files and independently qualified host-image bindings.

Inputs to this private adapter belong to the owning qualifier/runner. Neither a
constructor nor a child-provided observation can qualify its own whitelist.
Legacy three-key Python environment validation remains a separate interface.
"""
import ctypes
from ctypes import wintypes
from pathlib import Path
import stat
import sys
import sysconfig

from .binding import require
from .certification import _environment_current
from .codec import Invalid, canonical, decode, digest, integer, text
from .errors import Conflict
from .native_runtime import _manifest, _path, verify_tree
from .storage import _contained, _hash_file, blob_identity


SCHEMA = 'native-bootstrap-environment/1'
MAX_IMAGES = 1024
KERNEL_NAME = '_trf_stationary_native'
SUFFIX = sysconfig.get_config_var('EXT_SUFFIX')
KERNEL_FILE = KERNEL_NAME + SUFFIX
FIELDS = {'schema', 'runtime_id', 'manifest_sha256', 'module_files',
          'runtime_images', 'host_images'}


def _descriptor(value):
    require(type(value) is dict and set(value) == {'sha256', 'size'},
            'Exact native file descriptor required')
    blob_identity(value['sha256'])
    integer(value['size'], 'Native file size')
    return value


def _images(values):
    require(type(values) is list and len(values) <= MAX_IMAGES,
            'Bounded explicit image descriptors required')
    values = decode(canonical(values))
    seen = set()
    for value in values:
        require(type(value) is dict and set(value) == {'path', 'sha256', 'size'},
                'Exact native image descriptor required')
        path = text(value['path'], 'Native image path')
        require(Path(path).is_absolute(), 'Native image path must be absolute')
        key = str(Path(path).absolute()).casefold()
        require(key not in seen, 'Native image paths alias')
        seen.add(key)
        _descriptor({key: value[key] for key in ('sha256', 'size')})
    return values


def _read(path, *, single_link=True):
    try:
        value = path.lstat()
        require(stat.S_ISREG(value.st_mode) and (not single_link or value.st_nlink == 1),
                'Native dependency must be a regular file with its required link policy')
        checksum, size, _ = _hash_file(path)
        return {'sha256': checksum, 'size': size}
    except OSError as exc:
        raise Conflict('Native dependency file is unavailable') from exc


def _loaded_images():
    """Observe this Windows process using the documented loader snapshot API.

    Paths and current file hashes are observed, not relocated in-memory bytes.
    Repeated path snapshots detect library loads during inventory/hash work.
    """
    if sys.platform != 'win32':
        raise Invalid('Native loader inventory is not qualified on this platform')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.K32EnumProcessModules.argtypes = [wintypes.HANDLE,
        ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel.K32EnumProcessModules.restype = wintypes.BOOL
    kernel.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    kernel.GetModuleFileNameW.restype = wintypes.DWORD

    def paths():
        handles = (wintypes.HMODULE * MAX_IMAGES)()
        needed = wintypes.DWORD()
        if not kernel.K32EnumProcessModules(kernel.GetCurrentProcess(), handles,
                ctypes.sizeof(handles), ctypes.byref(needed)):
            raise ctypes.WinError(ctypes.get_last_error())
        require(needed.value <= ctypes.sizeof(handles)
                and needed.value % ctypes.sizeof(wintypes.HMODULE) == 0,
                'Native loader snapshot exceeds its envelope')
        result = []
        for handle in handles[:needed.value // ctypes.sizeof(wintypes.HMODULE)]:
            buffer = ctypes.create_unicode_buffer(32768)
            size = kernel.GetModuleFileNameW(handle, buffer, len(buffer))
            require(0 < size < len(buffer) - 1, 'Native loader path failed or was truncated')
            result.append(str(Path(buffer.value).resolve()))
        require(len({path.casefold() for path in result}) == len(result),
                'Native loader paths alias')
        return sorted(result, key=str.casefold)

    for _ in range(3):
        before = paths()
        result = [{'path': path, **_read(Path(path), single_link=False)} for path in before]
        if before == paths():
            return result
    raise Invalid('Native loader snapshot did not stabilize')


class NativeContext:
    def __init__(self, runtime_id, manifest, directory, host_images):
        self.runtime_id = blob_identity(runtime_id)
        self.manifest = _manifest(manifest)
        self.directory = Path(directory).absolute()
        _contained(self.directory.parent, self.directory)
        self.hosts = _images(host_images)
        self._host_map = {str(Path(value['path']).absolute()).casefold(): value for value in self.hosts}
        self._modules = {}

    @staticmethod
    def handles(name):
        return (name == 'numpy' or name.startswith('numpy.')
                or name == KERNEL_NAME or name.startswith(KERNEL_NAME + '.'))

    def _member(self, name, *, image=False):
        _path(name)
        files = self.manifest['files']
        require(name in files, 'Native file is outside the retained manifest')
        if image:
            allowed = (name == KERNEL_FILE or
                       name.startswith(('numpy/', 'numpy.libs/'))
                       and Path(name).suffix.lower() in ('.dll', '.pyd'))
        else:
            allowed = (name == KERNEL_FILE or name.startswith('numpy/')
                       and (name.endswith('.py') or name.endswith(SUFFIX)))
        require(allowed, 'Unsupported selected native file kind or namespace')
        return files[name]

    def _file(self, name, *, image=False):
        expected = self._member(name, image=image)
        path = _contained(self.directory, self.directory / name)
        require(_read(path) == expected, 'Selected native file differs from retained bytes')
        return expected

    def accepts(self, name, path):
        if not self.handles(name):
            return False
        require(not name.startswith(KERNEL_NAME + '.'), 'Unsupported native kernel submodule')
        path = Path(path).absolute()
        require(path.is_relative_to(self.directory), 'Handled native module is outside selected runtime')
        relative = path.relative_to(self.directory).as_posix()
        if name == KERNEL_NAME:
            require(relative == KERNEL_FILE, 'Kernel module filename differs')
        else:
            require(relative.startswith('numpy/'), 'NumPy module namespace differs')
        descriptor = self._file(relative)
        self._modules[relative] = descriptor
        return True

    def _host(self, value):
        key = str(Path(value['path']).absolute()).casefold()
        require(key in self._host_map, 'Native host image was not independently qualified')
        expected = self._host_map[key]
        claimed = {key: value[key] for key in ('sha256', 'size')}
        trusted = {key: expected[key] for key in ('sha256', 'size')}
        require(claimed == trusted, 'Native host image descriptor differs')
        # Only a trusted expected path may be opened, never an unknown child path.
        path = Path(expected['path'])
        _contained(path.parent, path)
        # OS component-store hardlinks are legitimate host files. The exact
        # independently qualified path and current bytes still have to match.
        require(_read(path, single_link=False) == trusted, 'Native host image changed since qualification')
        return expected

    def observation(self):
        runtime, host = {}, []
        for value in _images(_loaded_images()):
            path = Path(value['path']).absolute()
            if path.is_relative_to(self.directory):
                name = path.relative_to(self.directory).as_posix()
                expected = self._file(name, image=True)
                require({key: value[key] for key in ('sha256', 'size')} == expected,
                        'Observed runtime image descriptor differs')
                runtime[name] = expected
            else:
                host.append(self._host(value))
        for name, expected in self._modules.items():
            require(self._file(name) == expected,
                    'Selected module changed before native observation')
        result = {'schema': SCHEMA, 'runtime_id': self.runtime_id,
                  'manifest_sha256': digest(self.manifest), 'module_files': self._modules,
                  'runtime_images': runtime, 'host_images': host}
        return decode(canonical(result))

    def validate_bindings(self, observation):
        """Check retained metadata and host inputs without reading a cache."""
        require(type(observation) is dict and set(observation) == FIELDS,
                'Exact native environment observation required')
        require(observation['schema'] == SCHEMA and observation['runtime_id'] == self.runtime_id
                and observation['manifest_sha256'] == digest(self.manifest),
                'Native environment input binding differs')
        canonical(observation)
        for field, images in (('module_files', False), ('runtime_images', True)):
            values = observation[field]
            require(type(values) is dict and len(values) <= len(self.manifest['files']),
                    'Bounded native file observations required')
            for name, value in values.items():
                _descriptor(value)
                require(value == self._member(name, image=images), 'Native observed file differs')
        for value in _images(observation['host_images']):
            self._host(value)

    def validate(self, observation):
        self.validate_bindings(observation)
        for field, images in (('module_files', False), ('runtime_images', True)):
            for name, value in observation[field].items():
                require(value == self._file(name, image=images), 'Native observed file differs')
        # Include nonimported dependencies in the post-use integrity check.
        verify_tree(self.directory, self.manifest)


def current(environment, runtime_id, manifest, directory, host_images):
    """Validate child observations without importing its code in the controller."""
    try:
        require(type(environment) is dict and set(environment) ==
                {'identity', 'standard_library', 'isolation', 'native_runtime'},
                'Exact extended native environment required')
        base = {key: environment[key] for key in ('identity', 'standard_library', 'isolation')}
        if not _environment_current(base):
            return False
        NativeContext(runtime_id, manifest, directory, host_images).validate(environment['native_runtime'])
        return True
    except (Invalid, Conflict, OSError, KeyError, TypeError, AttributeError):
        return False


def inputs_current(environment, runtime_id, manifest, directory, host_images):
    """Pre-materialization inputs only; this cannot qualify cache use."""
    try:
        require(type(environment) is dict and set(environment) ==
                {'identity', 'standard_library', 'isolation', 'native_runtime'},
                'Exact extended native environment required')
        base = {key: environment[key] for key in ('identity', 'standard_library', 'isolation')}
        if not _environment_current(base):
            return False
        NativeContext(runtime_id, manifest, directory, host_images).validate_bindings(environment['native_runtime'])
        return True
    except (Invalid, Conflict, OSError, KeyError, TypeError, AttributeError):
        return False
