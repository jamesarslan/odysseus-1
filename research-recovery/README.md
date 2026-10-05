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
