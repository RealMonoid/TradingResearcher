# AmiBroker CLI access and programming notes

Scope: a small Windows automation tool for the installed AmiBroker 6.20.1 x86 build. It verifies a real import/exploration/export round trip. This is not the framework compiler, certified simulator or evidence engine. The user authorized CLI access and Binance test files on October 23, 2026.

## Commands

Run from the repository root with the installed Python (standard library only):

```powershell
python -B tools/amibroker/cli.py probe
python -B tools/amibroker/cli.py smoke-binance
python -B -m unittest discover -s tools/amibroker -p test_cli.py
```

`probe` reads application version, database path and symbol count. If AmiBroker is absent, the CLI starts its own hidden instance with an empty scratch database and closes that instance afterwards. If it is already running, the probe only reads it.

`smoke-binance` refuses to run while any AmiBroker process exists, creates a unique directory below `.local/amibroker/`, downloads one public BTCUSDT spot 15-minute archive for January 1, 2020, checks its provider SHA-256, validates all 96 candles, imports them and runs the supplied AFL exploration. It uses New Analysis / APX, not the obsolete `Analysis` execution interface. The result must match independent Python calculations. JSON output and the process exit code report PASS or failure; the run retains its inputs, APX, CSV, hashes and `result.json`. Normal completion closes only the CLI-owned instance. A controller timeout or cleanup failure fails the run; only the process started by that invocation is eligible for forced termination.

This controls a desktop application through a CLI; it is not a headless AmiBroker server. AmiBroker can still update its own global UI/preferences or show a modal error. Test market files are confined to the dedicated database, but arbitrary third-party AFL is not sandboxed by this utility. Existing user databases are not loaded by smoke runs. Full license entitlement, unattended-session support and broader adapter conformance are unverified.

## Verified control path and version boundaries

The controller uses 32-bit Windows Script Host (`SysWOW64/cscript.exe`) and `Broker.Application`. Direct PowerShell COM property access returned unusable results in this installation; JScript returned the real version and database. The implemented path is `AnalysisDocs.Open`, `Run(1)`, bounded `IsBusy` polling, `Export` and document close. `Run` means started, so completion and exported content are separately checked. The official model documents actions 0 scan, 1 exploration and 2 portfolio backtest, with further optimization actions. Only exploration is exercised here. [AmiBroker object model](https://www.amibroker.com/guide/objects.html).

Native batch entry points also exist:

```powershell
& 'C:\Program Files (x86)\AmiBroker\Broker.exe' /database 'C:\test-db' /runbatch 'C:\job.abb' /exit
```

This is a documentation example requiring real saved inputs, not a command to execute verbatim. The installed `ReleaseNotes.html` records these flags under 6.18.0, so they precede the installed 6.20.1 build. Direct `.abb` execution is documented but not tested here. An ABB sequence can load a saved APX, perform analysis and export; APX retains formula and analysis settings. [Vendor release note](https://www.amibroker.com/devlog/wp-content/uploads/2016/10/readme6180.html), [batch guide](https://www.amibroker.com/guide/h_batch.html).

The minimal APX writer uses field names inspected in the author's [APXCreator source](https://fastapi.metacpan.org/v1/source/BPRASAD/Amibroker-OLE-Interface-0.03/lib/Amibroker/OLE/APXCreator.pm), without importing that package or copying its settings template. This is an example implementation, not a vendor schema standard. The selected periodicity preset is checked by exporting `Interval() == 900`; a changed preset cannot silently pass as 15-minute data. The smoke profile does not establish valid defaults for portfolio backtests.

## Operation and AFL essentials

| Task | Practical starting point |
|---|---|
| Data | Choose a dedicated database; declare symbol, source, interval and timestamp semantics before import |
| Formula | Write an `.afl` file; in the UI use Formula Editor and Send to Analysis |
| Analysis | Set symbol scope, date range and periodicity; keep these settings with the APX |
| Exploration | `Filter` chooses rows and `AddColumn` specifies output; validate an exploration before trusting trading signals |
| Backtest | Define entry/exit signals, prices, delays, sizing, fees and portfolio constraints explicitly; then test accounting against known cases |
| Automation | Run from an external controller; do not invoke UI-changing automation from the formula being evaluated |

AFL primarily operates on arrays. `Close` is a series; `MA(Close, 3)` is a moving-average series. Ordinary scalar control flow and array selection differ: both branches of `IIf` are evaluated, so it is not a short-circuit guard for an invalid operation. [AFL array semantics](https://www.amibroker.com/guide/h_understandafl.html).

The tested [smoke formula](smoke.afl) exports prices, volume, a trailing average, prior close and interval. It deliberately contains no trading strategy. `Filter = 1` retains all bars; output precision is explicit. [Exploration tutorial](https://www.amibroker.com/guide/h_exploration.html).

Temporal programming rules matter: negative `Ref` offsets access prior observations; positive offsets access future ones. `LastValue` can expose the final observation to earlier bars. Both can create leakage if used incorrectly as decision inputs. [Ref reference](https://www.amibroker.com/guide/afl/ref.html), [LastValue reference](https://www.amibroker.com/guide/afl/lastvalue.html).

For a later close-signal/next-open execution fixture, specify delayed signals and open-price fills independently. `SetTradeDelays` shifts the four trade signal arrays; it does not shift sizing or other variables automatically. Actual next-bar fills, cash interactions, costs and stops still require independent conformance cases. They were not tested by this exploration. [SetTradeDelays reference](https://www.amibroker.com/guide/afl/settradedelays.html).

## Data and interpretation limits

The source is [Binance public data](https://github.com/binance/binance-public-data). The fixed 2020 fixture requires millisecond timestamps. The provider documents microseconds for spot archives from 2025; this converter deliberately rejects those instead of guessing units. It also rejects missing/duplicate bars, invalid OHLC ranges and nonfinite values. [Provider format description](https://raw.githubusercontent.com/binance/binance-public-data/master/README.md).

The importer uses an explicit [format file](binance.format), checked OHLCV and unscaled volume. This avoids relying on installed import defaults. [ASCII import reference](https://www.amibroker.com/guide/d_ascii.html).

The import labels each completed bar at its UTC end boundary: the source 00:00 opening bar is stamped 00:15, and the last bar is stamped January 2 at 00:00. This is a representation convention, not proof of historical publication latency. All timestamps and 900-second intervals must match exactly. OHLCV, prior close and MA3 must agree within `max(0.002, abs(expected)*2e-7)` to accommodate AmiBroker numeric storage/export. Missing warmup values must remain missing. The provider ZIP, raw CSV and checksum are retained unchanged in the local run.

The data are now exposed development fixtures. No 2024 assessment or 2025 reserved corroboration data were used. A present archive download is not a verified point-in-time vintage, and this test establishes no market hypothesis, trading profitability or statistical calibration. CMP-05 may eventually use an owned adapter; CMP-06 retains all scientific outcome authority. No AST-to-AFL compiler or free LLM discovery slice is implemented here.
