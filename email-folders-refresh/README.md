Standalone folder-discovery acceptance

Head: 7df09b48758873fcaf5f5fa195fc2448644704c5
Base: 2cd02da7fc5d500fa86511f2a36ddb431de532c8

A full uvicorn app using the committed read-only source was started with isolated SQLite/data storage and synthetic IMAP transport. In-process mail pollers and scheduled tasks were disabled. HTTP calls confirmed generic Sent resolves to the real localized mailbox and INBOX/Sent lists populate. Chromium opened the actual Mail window, selected Sent through its custom folder menu, confirmed the Sent badge and discovered wire-valued options, and checked the desktop and mobile views. No real Gmail connection was used for this merged-head run.

Desktop selector: desktop.png
Desktop message list: desktop-list.png
Mobile message list: mobile.png
Detailed assertions, synthetic IMAP transcript, source and image hashes: validation.json

The helper scripts contain only synthetic fixtures. No credentials, real messages, or external connections are included.

Final PR head 2c653210 only refreshes generated source-line references. All runtime hashes match the browser/API capture head, and 13 generated-reference tests pass.
