# Public source preview — 2026-10-29

Telegram/local-AirLLM game prototype. Full reachable source history reviewed for publication;
no identified credential or private user-save corpus blocker. Providers and real bot/model behavior
were not run or validated.

Restored missing source package save/manager.py and save/__init__.py from the local project, without
copying any game saves, .env, model weights or runtime data.
PASS — 2 regression tests verify a real GameState JSON save/load roundtrip, numeric/Unicode fields,
missing-save handling and deletion in a fresh temporary directory. Settings are stubbed so tests
do not read .env or write the normal saves location.
The complete bot, Telegram interaction, inference and UI remain unverified.
