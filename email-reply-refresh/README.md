Reply acceptance after the mail module migration

Browser capture head: 07cd2ea5e06da43472e2c322e45f701a31b7433a
Base: 2cd02da7fc5d500fa86511f2a36ddb431de532c8

The full branch source ran through uvicorn at a separate loopback port with a fresh database, synthetic Morgan/Taylor mail identities, no mailbox credentials, disabled background pollers/tasks, and a registered local model endpoint.

Reader guidance, editor guidance and typed-draft polishing used actual local generation through the real SSE endpoint. The late-edit case held a real generated response until an edit was made. Separate controlled responses tested bare Done and provisional reasoning/status followed by a disconnect without a terminal result. All six cases passed; no mail send was attempted.

The browser fixture returned success only for unrelated task notification-log POSTs to avoid an auth-disabled telemetry redirect in the upstream baseline. Mail list/read data was synthetic. The generation endpoint remained live except for explicitly labeled invalid-output fixtures.

Desktop and mobile captures contain synthetic identities only. validation.json records the cases, source hashes, screenshot hashes and dimensions. A later backend-only positional compatibility change is separately validated in api-validation.json; frontend capture files remain identical.
