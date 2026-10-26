"""Load the preserved pre-acceleration calculator without substituting its code."""
from contextlib import contextmanager
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'docs/reviews/implementation-2026-10-25/information-planning-source-before.zip'
ARCHIVE_SHA256='c437848d6e8285a1c64ed29d92437d431da1f055e6ee132bac8ccdc9c4363ea3'


@contextmanager
def fraction_reference():
    assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()==ARCHIVE_SHA256
    package='_retained_fraction_bootstrap'
    assert not any(n==package or n.startswith(package+'.') for n in sys.modules)
    with tempfile.TemporaryDirectory() as directory:
        destination=Path(directory)/'trading_researcher';destination.mkdir()
        with zipfile.ZipFile(ARCHIVE) as archive:
            for name in archive.namelist():
                parts=Path(name).parts
                if len(parts)==2 and parts[0]=='trading_researcher' and parts[1].endswith('.py'):
                    (destination/parts[1]).write_bytes(archive.read(name))
        spec=importlib.util.spec_from_file_location(package,destination/'__init__.py',
                                                   submodule_search_locations=[str(destination)])
        module=importlib.util.module_from_spec(spec);sys.modules[package]=module
        try:
            spec.loader.exec_module(module)
            yield importlib.import_module(package+'.stationary_bootstrap')
        finally:
            for name in list(sys.modules):
                if name==package or name.startswith(package+'.'):del sys.modules[name]


def binary_report(times):
    from datetime import datetime,timezone
    from bootstrap_support import report
    from trading_researcher.outcomes import materialize_reference
    template=report(times=2)['request']
    end=datetime.fromtimestamp(times*900,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    template['universe']['end']=end;template['as_of']=end
    catalog={'condition@1':{'type':'boolean','unit':None},'event@1':{'type':'boolean','unit':None}}
    rows=[{'time':i*900,'instrument':symbol,'features':{
        'condition@1':{'value':(i%8<4) if symbol=='A' else (i%5==0),'available_at':i*900},
        'event@1':{'value':i%7 in (0,1,4),'available_at':i*900}}} for i in range(times) for symbol in ('A','B')]
    return materialize_reference(template,catalog,rows)
