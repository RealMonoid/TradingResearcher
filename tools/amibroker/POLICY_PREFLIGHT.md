# Synthetic portfolio preflight

This is the bounded package-6 engineering check under research-contract/1.0
section 6 and D022/D042/D076. The existing research path has produced and retained
genuine descriptive reports. This check now asks whether the installed AmiBroker
6.20.1 can reproduce precisely declared execution and accounting facts. It does
not convert the observed paired price contrast into a trading policy or adopt a
new scientific profile. Vectorbt remains the recorded primary backend candidate.

[Requests](fixtures/policy_cases.json) and independently authored
[expectations](fixtures/policy_expected.json) are fixed before native execution.
Each synthetic asset has eight complete 15-minute UTC bars starting at
2023-01-01 00:00 UTC; labels denote bar opens. A listed signal is known only at
that bar's close and may fill at the following bar's open. This is an explicitly
idealized zero-latency discrete-bar convention, not proof of historical latency.
Complete-grid missingness fails before launch; no padding, nearest-bar substitution
or intrabar stop ordering is supported by this preflight.

The five cases cover timing, separate cost components, cash competition under
unique frozen ranks, same-bar proceeds available to a different instrument after
an exit, and an unfillable last-bar signal. Fixed integer quantities are long/flat
only, one position per asset, with no leverage, fractional sizing, shrinking,
stops, same-symbol simultaneous entry/exit, adaptive rule or open terminal
position. Unsupported requests fail explicitly. These constraints define the
test fixture coverage, not a closed catalog for LLM hypothesis discovery.

Commission applies independently at each actual adverse fill's notional.
Spread, slippage and impact are separately named one-way basis-point adjustments;
their sum increases entry price and decreases exit price. Zero values are explicit
synthetic scenarios. Real account fees, executable spread, impact and net-value
hurdles remain unknown. No economic claim is authorized.

The generated AFL delegates trade processing to AmiBroker's native portfolio
backtester. It exports actual per-bar cash and open positions, plus native trade
prices, commissions and PnL. The declared close mark is derived in AFL from native
cash plus actual native open quantities times native closing quotes. The separate
`native_equity.csv` retains unmodified `bo.Equity`: the observed cost case has a
different native valuation while positions are open. The difference is consistent
with a hypothetical exit commission, but this observation does not establish a
universal portfolio-equity formula. Python validates the declared close marks
against the independent expectations; it does not replace native results with its
own simulated accounting. Ordinal indices, UTC labels, symbols, quantities and
counts must match exactly. Predeclared absolute tolerances are 0.00001 for prices
and 0.001 currency units for cash, equity, fees and PnL. These cover this small
numerical fixture only; wider numerical adequacy remains unverified.

The [controller](policy_preflight.py) reuses the existing CLI's executable,
process inventory and guarded probe/quit calls. Native runs refuse an existing
AmiBroker process and use a unique empty database below `.local/amibroker/`.
The [worker](policy_worker.js) checks the exact database and synthetic inventory
before import, waits for each analysis completion, exports raw signals and trade
lists, and closes its analysis document. Each analysis has a 30-second limit,
the worker has a 75-second limit and the controller an 80-second call timeout.
Cleanup may terminate only the process started by that invocation. AmiBroker's
own global UI/preferences are outside database isolation; no claim of application
sandboxing or portable license entitlement is made.

Before launch, each run retains its request, AFL/APX, input CSV, executable hash,
adapter hashes and expectation hash. Results, errors, output files, times and
cleanup failures remain in that exclusive run directory. Five cases are planned,
each twice from a fresh application/database for replay comparison. At most two
additional diagnosed repair attempts are allocated; two iterations without
meaningful improvement stop expansion. No provider calls, market downloads,
production research-registry changes or protected-data access are needed.

The [October 31 closeout](../../docs/reviews/implementation-2026-10-25/amibroker-preflight-2026-10-31.json)
passes all five cases twice under the final sources; six raw CSV exports per case
are byte-identical between repeats. The original case and independent expectation
files and their tolerances remain unchanged. Earlier failed attempts and interim
source versions remain retained. The user's later explicit instruction to fix the
adapter authorized the diagnosed follow-up rather than the proposed gap closeout;
the recorded original repair allowance was not silently reset.

The native repairs include APX string escaping beyond XML, preserving the observed
APX settings order, applying symbol-only Hold/Early options in symbol context,
and the explicit equity representation above. The APX fixes use the author's
[retained writer example](https://fastapi.metacpan.org/v1/source/BPRASAD/Amibroker-OLE-Interface-0.03/lib/Amibroker/OLE/APXCreator.pm)
as implementation guidance and actual native output as compatibility evidence.
The synthetic importer supplies dummy volume; the native volume-size cap is
explicitly disabled for these fixed-quantity accounting cases. This is not a
liquidity model. Native quantities must be integral before integer CSV formatting.
Timeout output and per-call stages are retained even when a modal blocks COM.

This preflight does not complete package 6's separately frozen policy trial,
scientific calibration, realistic-cost assessment or portfolio profitability.
The sole implementation plan records current outcomes and the next unmet gate.

The vendor documents the asynchronous portfolio action in
[AnalysisDoc](https://www.amibroker.com/guide/objects.html), native cash/trade
access in the [backtester interface](https://www.amibroker.com/guide/a_custombacktest.html),
explicit accounting options in [SetOption](https://www.amibroker.com/guide/afl/setoption.html)
and signal-only shifting in [SetTradeDelays](https://www.amibroker.com/guide/afl/settradedelays.html).
Those API descriptions guide the implementation; only the local conformance
results establish what this installed version actually did.
