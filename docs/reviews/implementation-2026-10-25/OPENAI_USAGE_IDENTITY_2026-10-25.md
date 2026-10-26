# Model identity and call timestamps

Date: October 25, 2026. This supplement preserves the original usage observation and ledger bytes.
The table joins already retained API response metadata to original admission timestamps.
Catalog name/version is a separately sourced public label, not an immutable model revision.

| Admission time (UTC) | Perspective | Requested model | Reported model | Input | Output |
|---|---|---|---|---:|---:|
| 2026-10-25T17:19:02Z | first | gpt-6.1-sol | gpt-6.1-sol | 476 | 14 |
| 2026-10-25T17:19:05Z | first | gpt-6.1-sol | gpt-6.1-sol | 543 | 53 |
| 2026-10-25T17:19:09Z | second | gpt-6.1-sol | gpt-6.1-sol | 476 | 14 |
| 2026-10-25T17:19:12Z | second | gpt-6.1-sol | gpt-6.1-sol | 543 | 53 |

Public model: **GPT-6.1 Sol**, catalog version **6.1**. [Official catalog](https://developers.openai.com/api/docs/models/gpt-6.1-sol). The retained responses report `gpt-6.1-sol`; an immutable snapshot is **UNKNOWN**.

The old records have no retained settlement time or catalog fields. Their original rows remain unchanged. This supplement does not silently populate missing historical receipt fields.

New calls automatically store catalog identity, requested/reported model identifiers, prompt version, admission time and local settlement time. Times are ISO8601 with the explicit UTC marker `Z`; they are host accounting times, not provider execution timestamps.

**Consumption remains 2,172 tokens; conservative currency bound remains USD 0.006435.** No new model call or charge was created for this supplement.

[Exact observation](provider-identity-observation.json) · [Report interface](../../../trading_researcher/OPENAI.md)
