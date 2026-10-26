# Independent Binance archive expectations

The adjacent `reference_binance_cases.json` was authored without reading the Binance archive implementation. It contains synthetic CSV and ZIP bytes, hand-calculated parsed values, and explicit rejection cases. It does not provide a scientific certificate, market evidence, legal advice, or verified historical availability.

Sources checked on October 25, 2026: the official [public-data README](https://github.com/binance/binance-public-data/blob/master/README.md) and [Spot REST market-data documentation](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints). The README identifies the 2025 spot timestamp-unit change, the kline columns, accompanying SHA-256 files and possible later archive revisions. The fixture's engineering restrictions below are deliberately separate from those source facts.

## Time and value mapping

The supported archive identity explicitly names the symbol, `15m` interval and calendar month. For pre-2025 spot archives the timestamp factor is 1,000; from January 2025 it is 1,000,000. Do not select the factor opportunistically from individual rows. The archive's declared month and exact integer timestamp range must agree.

For an aligned bar, the source's inclusive final tick must equal `open_raw + 900 * factor - 1`. Parsed `open_time` is `open_raw / factor`; parsed `end_time` is exactly 900 seconds later. These divisions must be exact, without floating-point conversion or rounding. The normalized reference row uses `end_time`, never the source open timestamp. The original raw opening and inclusive closing values remain recoverable from the retained archive.

OHLC and volume values remain exact ordinary decimal strings, with unnecessary trailing fractional zeroes removed. Prices must be positive and obey `low <= min(open, close) <= max(open, close) <= high`. Volume and quote quantities are nonnegative; the respective taker-buy quantities cannot exceed their totals. Trade count is a nonnegative integer. The ignored twelfth source column is retained in the archive and introduces no feature meaning. The fixtures do not invent a tolerance rule for rounded quote/base identities or reconstruct individual trades.

Missing bars remain absent. A gap between 00:00 and 00:30 source opens does not create a 00:15 source bar. Empty input is rejected; a valid zero-activity bar is distinct from absence. Duplicate/reversed opens, wrong column counts, unsupported numeric spellings and invalid times fail rather than being repaired. The final normalized timestamp can fall at the next month's or partition's boundary. Parsing retains that timestamp; subsequent selection must explicitly account for excluded boundary bars without relabeling prior-partition information.

## Units and availability

Use symbol-qualified versioned feature identifiers, for example `BTCUSDT.close@binance-spot-15m-v1`. BTC price fields carry `USDT/BTC`, and BTC base-quantity fields carry `BTC`. ETH uses `USDT/ETH` and `ETH`. Quote-volume fields carry `USDT`; trade counts carry `count`. The current expression engine treats these strings as unit identities. This mapping prevents accidental equality of unlike base quantities without adding compound-unit algebra. It does not permit unsupported multiplication merely because dimensional cancellation looks plausible.

Raw parsing makes no historical release claim. A subsequent explicitly selected `delay_seconds` scenario maps `available_at = end_time + delay_seconds`, with `availability.basis = assumed`, historical publication unknown and scientific readiness false. Delays 0 and 5 in the fixtures are test parameters, not recommended or verified latency assumptions. Neither present retrieval time nor ZIP metadata is evidence that the exact archive vintage was available at each historical bar close. Preserve retrieval time and source rights separately; these fixtures do not determine dataset licensing.

## Container and checksum boundaries

The synthetic ZIP cases use fixed stored entries and fixed timestamps. Each archive's base64 bytes and SHA-256 are supplied in the fixture. A checksum must identify those exact ZIP bytes and the exact expected archive basename; extra records or malformed declarations fail. The archive reader accepts one exact expected CSV member and rejects extra, duplicate, misnamed, traversal or malformed members. These are bounded adapter rules, not claims that every possible ZIP layout is unsafe. Read the member as bytes; no filesystem extraction is needed.

Fixture failure reasons are explanatory labels. A test adapter may map them to the application's existing structured error types; acceptance/rejection and exact expected values must remain fixed. The `availability_scenario` cases are a contract for the later row-construction seam, separate from raw CSV parsing.

Source checksums authenticate content against the retrieved checksum assertion; they do not independently establish provider identity, historical vintage, lawful use, price correctness, or scientific suitability. Real acquisition still needs retained source URLs, exact response bytes, checksum responses, retrieval metadata, revision provenance and explicit rights/availability qualifications. Resource limits and network redirect/host checks need separate integration tests; no large ZIP or live-provider run is represented by this bundle.
