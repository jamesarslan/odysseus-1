# Research pipeline acceptance evidence

Public source head: `956bfdff`, based on `dev` at `2992bf6d`.

These captures come from a separate authenticated Docker app on loopback port
7001 with a private database snapshot. Its eight runtime source files exactly
match the public research branch; it does not include the separate PDF fallback.

The fresh local-server run completed in 343.5 seconds with four findings from ten
analyzed pages. Four URLs include two forms of the same original paper. This
checks collection, extraction, completion, persistence and rendering; model
factual accuracy and requested-source coverage remain limited. The report
misattributes one source and contains unsupported hardware/safety statements.

The search failure is a copy of the original real failed research result. The
extraction failure is explicitly a controlled fixture persisted through the
public-head handler with simulated extraction responses. It is not a claimed
live provider outage.

Desktop and mobile screenshots were visually checked. Unrelated private chat,
account information, other reports and model labels were hidden only for the
captures. The report references expose only the public topic and public sources.
`validation.json` contains viewport, API/DOM assertions and artifact hashes.

Refresh after current dev integration

Final PR head: e7e0112a6f323db339b6a3db87e08736116d65c0. The two research-refresh-history images and validation-refresh.json retain three actual synthetic runtime outcomes: a correctly explained empty extraction, two requested primary pages with findings/report, and one search-found PDF finding preserved after incomplete synthesis. The searched question still did not reliably retrieve the requested primary pages. Final CSS fixes failure-text overflow on mobile; before/after browser measurements cover 1440, 390 and 375px widths. Backend capture and test heads are explicitly recorded; no model research was rerun for the CSS-only change. These new files do not replace the historical screenshots/validation above.
