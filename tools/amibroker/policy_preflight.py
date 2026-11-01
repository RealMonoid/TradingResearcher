"""Frozen synthetic portfolio conformance; no market policy or scientific verdict."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

from cli import EXE, HERE, ROOT, host_call, running_brokers

PROFILE = 'synthetic-long-flat/1'
PRICE_TOLERANCE = Decimal('0.00001')
MONEY_TOLERANCE = Decimal('0.001')

def number(value):
    if type(value) is not str or not re.fullmatch(r'\d+(?:\.\d+)?', value):
        raise ValueError('A finite nonnegative decimal string is required')
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError('Invalid decimal') from error
    if not result.is_finite() or result > 1000000:
        raise ValueError('Numeric fixture envelope exceeded')
    return result

def exact_fields(value, fields):
    if type(value) is not dict or set(value) != set(fields.split()):
        raise ValueError('Unsupported or incomplete fixture fields')

def validate_case(case):
    exact_fields(case, 'schema id synthetic start_utc bar_seconds initial_cash costs assets')
    if (case['schema'] != PROFILE or case['synthetic'] is not True
            or case['start_utc'] != '2023-01-01T00:00:00Z' or type(case['bar_seconds']) is not int
            or case['bar_seconds'] != 900 or type(case['id']) is not str
            or not re.fullmatch(r'[a-z_]{1,40}', case['id']) or number(case['initial_cash']) <= 0):
        raise ValueError('Only the declared synthetic quarter-hour profile is supported')
    costs = case['costs']
    exact_fields(costs, 'commission_bps spread_bps slippage_bps impact_bps basis valid_for')
    if costs['basis'] != 'synthetic_per_fill_notional' or costs['valid_for'] != 'fixture_only':
        raise ValueError('Costs must be explicitly synthetic per-fill scenarios')
    if any(number(costs[k]) > 100 for k in ('commission_bps','spread_bps','slippage_bps','impact_bps')):
        raise ValueError('Cost scenario exceeds the fixture envelope')
    assets = case['assets']
    if type(assets) is not list or not 1 <= len(assets) <= 2:
        raise ValueError('One or two fixed synthetic assets required')
    symbols, ranks = set(), set()
    for asset in assets:
        exact_fields(asset, 'symbol rank quantity buy sell bars')
        if asset['symbol'] not in ('TRF_A','TRF_B') or asset['symbol'] in symbols:
            raise ValueError('Unsupported or duplicate synthetic asset')
        symbols.add(asset['symbol'])
        for key in ('rank','quantity'):
            if type(asset[key]) is not int or not 1 <= asset[key] <= 1000:
                raise ValueError('Positive integer rank and fixed quantity required')
        if asset['rank'] in ranks:
            raise ValueError('Shared cash requires an unambiguous frozen rank')
        ranks.add(asset['rank'])
        for key in ('buy','sell'):
            values = asset[key]
            if (type(values) is not list or any(type(v) is not int or not 0 <= v < 8 for v in values)
                    or values != sorted(set(values))):
                raise ValueError('Invalid signal indices')
        if set(asset['buy']) & set(asset['sell']):
            raise ValueError('Same-symbol simultaneous signals are unsupported')
        opened = False
        for i in range(7):
            if i in asset['sell']:
                if not opened: raise ValueError('Unmatched exit signal')
                opened = False
            if i in asset['buy']:
                if opened: raise ValueError('Repeated entries are outside this fixture profile')
                opened = True
        if opened or 7 in asset['sell']:
            raise ValueError('Unclosed positions and final-bar exits are unsupported')
        if type(asset['bars']) is not list or len(asset['bars']) != 8:
            raise ValueError('Missing bars cannot be padded or skipped')
        for bar in asset['bars']:
            exact_fields(bar, 'open high low close')
            o,h,l,c = (number(bar[k]) for k in ('open','high','low','close'))
            if min(o,h,l,c) <= 0 or l > min(o,c) or h < max(o,c):
                raise ValueError('Invalid OHLC range')
    return case

def load_cases():
    data = json.loads((HERE/'fixtures/policy_cases.json').read_text(encoding='utf-8'))
    exact_fields(data, 'schema cases')
    if data['schema'] != 'amibroker-synthetic-preflight/1' or type(data['cases']) is not list:
        raise ValueError('Wrong fixture inventory')
    cases = [validate_case(c) for c in data['cases']]
    if len(cases) != 5 or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('The complete fixed five-case inventory is required')
    return cases

def labels(case):
    start = datetime.fromisoformat(case['start_utc'].replace('Z','+00:00'))
    return [(start+timedelta(seconds=i*900)).strftime('%Y-%m-%dT%H:%M:%SZ') for i in range(8)]

def afl_path(path):
    value = str(Path(path).resolve())
    if any(c in value for c in ('"','\n','\r')):
        raise ValueError('Unsafe AFL path')
    return value.replace('\\','\\\\')

def build_formula(case, output_dir):
    validate_case(case)
    costs = case['costs']
    adverse = sum(number(costs[k]) for k in ('spread_bps','slippage_bps','impact_bps')) / 10000
    options = {'InitialEquity':case['initial_cash'], 'AccountMargin':100, 'FuturesMode':0,
        'InterestRate':0, 'MaxOpenPositions':len(case['assets']), 'AllowPositionShrinking':0,
        'AllowSameBarExit':0, 'ReverseSignalForcesExit':0, 'PriceBoundChecking':0,
        'UsePrevBarEquityForPosSizing':1, 'MinShares':1, 'MinPosValue':0, 'SettlementDelay':0,
        'CommissionMode':1, 'CommissionAmount':number(costs['commission_bps'])/100,
        'HoldMinBars':0, 'HoldMinDays':0, 'EarlyExitBars':0, 'EarlyExitDays':0, 'EarlyExitFee':0,
        'DisableRuinStop':1, 'ActivateStopsImmediately':0, 'EveryBarNullCheck':1,
        'GenerateReport':0, 'PortfolioReportMode':0, 'RefreshWhenCompleted':0, 'MCEnable':0}
    parts = ['// Fixed synthetic request. No arbitrary user AFL or market evidence.']
    per_symbol = {'HoldMinBars','HoldMinDays','EarlyExitBars','EarlyExitDays','EarlyExitFee'}
    parts += [f'SetOption("{key}", {value});' for key,value in options.items() if key not in per_symbol]
    parts.append('if(Status("action")!=actionPortfolio) {')
    parts += [f'SetOption("{key}", {value});' for key,value in options.items() if key in per_symbol]
    parts.append('}')
    parts += ['SetBacktestMode(backtestRegular);', 'SetTradeDelays(1,1,1,1);',
        'SetBarsRequired(sbrAll,sbrAll);', 'SetCustomBacktestProc("");',
        'RoundLotSize=1; TickSize=0; PointValue=1; MarginDeposit=0;',
        'Buy=Sell=Short=Cover=0; PositionScore=0; SetPositionSize(1,spsShares);',
        f'BuyPrice=Open*(1+{adverse}); SellPrice=Open*(1-{adverse});',
        'ShortPrice=CoverPrice=Open; b=BarIndex();']
    for stop in ('stopTypeLoss','stopTypeProfit','stopTypeTrailing','stopTypeNBar'):
        parts.append(f'ApplyStop({stop},stopModeDisable,0);')
    for asset in case['assets']:
        buy = ' OR '.join('b=='+str(i) for i in asset['buy']) or '0'
        sell = ' OR '.join('b=='+str(i) for i in asset['sell']) or '0'
        parts.append(f'if(Name()=="{asset["symbol"]}") {{ Buy={buy}; Sell={sell}; '
            f'PositionScore={asset["rank"]}; SetPositionSize({asset["quantity"]},spsShares); }}')
    parts += ['SetOption("NoDefaultColumns",True); Filter=1;',
        'AddTextColumn(Name(),"Symbol"); AddColumn(b,"Index",1.0);',
        'AddColumn(DateNum(),"Day",1.0); AddColumn(TimeNum(),"Time",1.0);',
        'AddColumn(Open,"Open",1.8); AddColumn(Close,"Close",1.8);',
        'AddColumn(Buy,"BuySignal",1.0); AddColumn(Sell,"SellSignal",1.0);',
        'AddColumn(PositionScore,"Rank",1.0); AddColumn(Interval(),"Interval",1.0);',
        'if(Status("action")==actionPortfolio) {', 'bo=GetBacktesterObject(); bo.PreProcess(); dt=DateTime();',
        f'fs=fopen("{afl_path(Path(output_dir)/"state.csv")}","w");',
        f'fp=fopen("{afl_path(Path(output_dir)/"positions.csv")}","w");',
        f'fn=fopen("{afl_path(Path(output_dir)/"native_equity.csv")}","w");',
        'if(!fs OR !fp OR !fn) Error("Cannot create owned state exports");',
        'fputs("index,timestamp,cash,equity\\n",fs); fputs("index,symbol,quantity\\n",fp);',
        'fputs("index,timestamp,equity\\n",fn);',
        'for(i=0;i<BarCount;i++) { bo.ProcessTradeSignals(i);',
        'mark=bo.Cash;',
        'for(pos=bo.GetFirstOpenPos();pos;pos=bo.GetNextOpenPos()) {',
        'if(pos.Shares!=floor(pos.Shares)) Error("Nonintegral native position quantity");',
        'mark=mark+pos.Shares*pos.GetPrice(i,"C");',
        'fputs(StrFormat("%.0f,",i)+pos.Symbol+StrFormat(",%.0f\\n",pos.Shares),fp);',
        '}',
        'fputs(StrFormat("%.0f,",i)+DateTimeFormat("%Y-%m-%dT%H:%M:%SZ",dt[i])+StrFormat(",%.8f,%.8f\\n",bo.Cash,mark),fs);',
        'fputs(StrFormat("%.0f,",i)+DateTimeFormat("%Y-%m-%dT%H:%M:%SZ",dt[i])+StrFormat(",%.8f\\n",bo.Equity),fn);',
        '} fclose(fs); fclose(fp); fclose(fn); bo.PostProcess();',
        f'ft=fopen("{afl_path(Path(output_dir)/"trades.csv")}","w");',
        'if(!ft) Error("Cannot create owned trade export");',
        'fputs("symbol,entry_timestamp,exit_timestamp,quantity,entry_price,exit_price,entry_fee,exit_fee,pnl\\n",ft);',
        'for(tr=bo.GetFirstTrade();tr;tr=bo.GetNextTrade()) {',
        'if(tr.Shares!=floor(tr.Shares)) Error("Nonintegral native trade quantity");',
        'fputs(tr.Symbol+","+DateTimeFormat("%Y-%m-%dT%H:%M:%SZ",tr.EntryDateTime)+","+DateTimeFormat("%Y-%m-%dT%H:%M:%SZ",tr.ExitDateTime)',
        '+StrFormat(",%.0f,%.8f,%.8f,%.8f,%.8f,%.8f\\n",tr.Shares,tr.EntryPrice,tr.ExitPrice,tr.GetCommission(False),tr.GetCommission(True)-tr.GetCommission(False),tr.GetProfit()),ft);',
        '} fclose(ft); }']
    return '\n'.join(parts)+'\n'

def read_csv(path, fields):
    content = Path(path).read_text(encoding='utf-8-sig')
    lines = content.splitlines()
    if not lines: raise ValueError('Empty native export')
    delimiter = ';' if lines[0].count(';') > lines[0].count(',') else ','
    reader = csv.DictReader(lines, delimiter=delimiter)
    if reader.fieldnames != fields.split(): raise ValueError('Unexpected native export columns')
    rows = list(reader)
    if any(None in row or None in row.values() for row in rows): raise ValueError('Malformed native CSV')
    return rows

def parse_native(case, output_dir):
    validate_case(case); output_dir = Path(output_dir); times = labels(case)
    states = read_csv(output_dir/'state.csv', 'index timestamp cash equity')
    if len(states) != 8: raise ValueError('Incomplete native state trace')
    symbols = [a['symbol'] for a in case['assets']]
    rows = []
    for i,row in enumerate(states):
        if row['index'] != str(i) or row['timestamp'] != times[i]: raise ValueError('Native time grid differs')
        rows.append({'timestamp':row['timestamp'], 'cash':row['cash'], 'equity':row['equity'],
            'positions':dict.fromkeys(symbols,0)})
    seen = set()
    for pos in read_csv(output_dir/'positions.csv', 'index symbol quantity'):
        i = int(pos['index']); symbol = pos['symbol']; q = int(pos['quantity'])
        if not 0 <= i < 8 or symbol not in symbols or (i,symbol) in seen or q <= 0:
            raise ValueError('Invalid native open position')
        seen.add((i,symbol)); rows[i]['positions'][symbol] = q
    trades = []
    for trade in read_csv(output_dir/'trades.csv', 'symbol entry_timestamp exit_timestamp quantity entry_price exit_price entry_fee exit_fee pnl'):
        entry = times.index(trade.pop('entry_timestamp')); end = times.index(trade.pop('exit_timestamp'))
        trades.append({**trade,'entry_index':entry,'exit_index':end,'quantity':int(trade['quantity'])})
    return {'rows':rows,'trades':trades}

def verify_result(actual, expected):
    exact_fields(actual, 'rows trades'); exact_fields(expected, 'rows trades')
    if any(type(value[key]) is not list for value in (actual,expected) for key in ('rows','trades')):
        raise ValueError('Native result rows and trades must be lists')
    if len(actual['rows']) != len(expected['rows']) or len(actual['trades']) != len(expected['trades']):
        raise ValueError('Native case/trade count differs from independent expectations')
    for kind in ('rows','trades'):
        for got,want in zip(actual[kind],expected[kind]):
            if type(got) is not dict or set(got) != set(want): raise ValueError('Native result fields differ')
            for key,value in want.items():
                if key in ('cash','equity','entry_fee','exit_fee','pnl','entry_price','exit_price'):
                    try: observed, reference = Decimal(str(got[key])), Decimal(str(value))
                    except InvalidOperation as error: raise ValueError('Invalid native numeric cell') from error
                    tolerance = PRICE_TOLERANCE if key.endswith('price') else MONEY_TOLERANCE
                    if not observed.is_finite() or not reference.is_finite() or abs(observed-reference) > tolerance:
                        raise ValueError('Native '+key+' differs from independent expectation')
                elif key in ('quantity','entry_index','exit_index') and type(got[key]) is not int:
                    raise ValueError('Native integer field has the wrong type')
                elif key == 'positions' and (type(got[key]) is not dict
                        or any(type(v) is not int for v in got[key].values()) or got[key] != value):
                    raise ValueError('Native positions differ from independent expectation')
                elif got[key] != value:
                    raise ValueError('Native '+key+' differs from independent expectation')
    return {'status':'PASS','rows':len(actual['rows']),'trades':len(actual['trades']),
        'price_absolute_tolerance':str(PRICE_TOLERANCE),'money_absolute_tolerance':str(MONEY_TOLERANCE)}

def verify_signals(case, path):
    rows = read_csv(path, 'Symbol Index Day Time Open Close BuySignal SellSignal Rank Interval')
    expected = {(a['symbol'],str(i)):(a,bar) for a in case['assets'] for i,bar in enumerate(a['bars'])}
    if len(rows) != len(expected): raise ValueError('Incomplete native signal export')
    seen = set()
    for row in rows:
        key = row['Symbol'],row['Index']
        if key not in expected or key in seen: raise ValueError('Unexpected or duplicate signal row')
        seen.add(key); asset,bar = expected[key]; i = int(row['Index'])
        for field,value in {'Day':'1230101','Time':str(i//4*10000+(i%4)*1500),
                'BuySignal':str(int(i in asset['buy'])),'SellSignal':str(int(i in asset['sell'])),
                'Rank':str(asset['rank']),'Interval':'900'}.items():
            if row[field] != value: raise ValueError('Native signal/time mismatch: '+field)
        for field in ('Open','Close'):
            if abs(Decimal(row[field])-Decimal(bar[field.lower()])) > PRICE_TOLERANCE:
                raise ValueError('Native imported price differs')

def write_inputs(case, run):
    formula = build_formula(case, run)
    # APX applies its own string escaping after XML decoding. Preserve Windows
    # formula bytes and encode line breaks/backslashes for that second layer.
    (run/'policy.afl').write_bytes(formula.replace('\n','\r\n').encode('ascii'))
    with (run/'import.csv').open('w',newline='',encoding='ascii') as out:
        writer = csv.writer(out)
        for asset in case['assets']:
            for timestamp,bar in zip(labels(case),asset['bars']):
                writer.writerow([asset['symbol'],timestamp[:10],timestamp[11:19],
                    *[bar[k] for k in ('open','high','low','close')],1])
    root = ET.Element('AmiBroker-Analysis', CompactMode='0'); general = ET.SubElement(root,'General')
    encoded_formula = formula.replace('\\','\\\\').replace('\n',r'\r\n').replace('\t',r'\t')
    for k,v in {'FormatVersion':'1','Symbol':case['assets'][0]['symbol'],
            'FormulaPath':str(run/'policy.afl').replace('\\','\\\\'),
            'FormulaContent':encoded_formula,'ApplyTo':'0','RangeType':'0','RangeAmount':'1'}.items():
        ET.SubElement(general,k).text = v
    settings = ET.SubElement(root,'BacktestSettings')
    for key,value in {'TradeFlags':'1','Periodicity':'3','UseConstantPriceArrays':'0',
            'AlignToReferenceSymbol':'0','AddFutureBars':'0','LimitTradeSizeAsPctVol':'0'}.items():
        ET.SubElement(settings,key).text = value
    ET.ElementTree(root).write(run/'policy.apx',encoding='utf-8',xml_declaration=True)

def execute_case(case, expected, repeat):
    validate_case(case)
    if running_brokers(): raise RuntimeError('Existing AmiBroker instance: no isolated run admitted')
    base = ROOT/'.local/amibroker'; base.mkdir(parents=True,exist_ok=True)
    (base/'.gitignore').write_text('*\n',encoding='ascii')
    run = base/('policy-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    run.mkdir(); db = run/'database'; db.mkdir()
    write_inputs(case,run)
    (run/'request.json').write_text(json.dumps(case,indent=2)+'\n',encoding='utf-8')
    report = {'status':'FAIL','profile':PROFILE,'case_id':case['id'],'repeat':repeat,'run_directory':str(run),
        'started_at_utc':datetime.now(timezone.utc).isoformat(),'scientific_readiness':False,
        'executable_sha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),
        'sources':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in
            ('policy_preflight.py','policy_worker.js','cli.py','worker.js','binance.format','fixtures/policy_cases.json','fixtures/policy_expected.json')}}
    (run/'manifest-before.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    process = None; started = time.monotonic()
    try:
        startup = subprocess.STARTUPINFO(); startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW; startup.wShowWindow = 0
        process = subprocess.Popen([str(EXE),'/database',str(db)],cwd=EXE.parent,startupinfo=startup)
        time.sleep(2)
        if process.poll() is not None: raise RuntimeError('Owned application exited before automation')
        report['application'] = host_call('probe',db)
        if report['application']['version'] != '6.20.1': raise RuntimeError('Installed version differs from preflight')
        cmd = [str(Path(os.environ['WINDIR'])/'SysWOW64/cscript.exe'),'//nologo','//T:75',str(HERE/'policy_worker.js'),
            str(db),str(run/'import.csv'),str(HERE/'binance.format'),str(run/'policy.apx'),str(run/'signals.csv'),
            str(run/'backtest.csv'),str(len(case['assets']))]
        call = subprocess.run(cmd,capture_output=True,text=True,timeout=80)
        (run/'worker-output.txt').write_text(call.stdout+'\n'+call.stderr,encoding='utf-8')
        if call.returncode: raise RuntimeError('Native worker failed: '+str(call.returncode)+' '+call.stdout.strip())
        verify_signals(case,run/'signals.csv')
        actual = parse_native(case,run)
        native_equity = read_csv(run/'native_equity.csv', 'index timestamp equity')
        if len(native_equity) != 8 or any(row['index']!=str(i) or row['timestamp']!=labels(case)[i]
                or not Decimal(row['equity']).is_finite() for i,row in enumerate(native_equity)):
            raise ValueError('Incomplete raw native equity trace')
        report['native_equity_trace'] = native_equity
        report['equity_basis'] = 'Actual native cash plus native open quantities times native close quotes; raw bo.Equity retained separately.'
        report['verification'] = verify_result(actual,expected)
        report['actual'] = actual
        if any(hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=sha for name,sha in report['sources'].items()):
            raise RuntimeError('Adapter or frozen fixtures changed during native execution')
        report['status'] = 'PASS'
    except subprocess.TimeoutExpired as error:
        def retained(value):
            return value.decode('utf-8',errors='replace') if isinstance(value,bytes) else (value or '')
        (run/'worker-output.txt').write_text(retained(error.stdout)+'\n'+retained(error.stderr),encoding='utf-8')
        report['error'] = str(error)
        report['timeout_output_retained'] = True
    except Exception as error:
        report['error'] = str(error)
    finally:
        if process is not None and process.poll() is None:
            try:
                host_call('quit',db); process.wait(timeout=10)
            except Exception as error:
                report['status']='FAIL'; report['cleanup_error']=str(error); process.kill(); process.wait(timeout=10)
        report['wall_seconds']=time.monotonic()-started
        report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        report['artifacts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in run.iterdir() if p.is_file()}
        (run/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=[c['id'] for c in load_cases()], required=True)
    parser.add_argument('--repeat', type=int, choices=(1,2), default=1)
    args = parser.parse_args()
    expected = json.loads((HERE/'fixtures/policy_expected.json').read_text(encoding='utf-8'))['cases'][args.case]
    case = next(c for c in load_cases() if c['id']==args.case)
    report = execute_case(case,expected,args.repeat)
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['status']=='PASS' else 1)

if __name__ == '__main__': main()
