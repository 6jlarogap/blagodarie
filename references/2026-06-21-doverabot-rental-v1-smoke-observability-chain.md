# Doverabot Rental V1 Smoke Observability Chain

Date: 2026-06-21
Status: implemented; runtime deploy not required
Parent project: [projects/doverabot-revival.md](../projects/doverabot-revival.md)
Go-next chain: [2026-06-21-doverabot-go-next-chain.md](2026-06-21-doverabot-go-next-chain.md)
Slug: `doverabot-rental-v1-smoke-observability`

## Scope

- Add low-friction smoke coverage for rental search, map exposure,
  booking/reservation callback surfaces, and payment-proof handoff.
- Prefer source-level mocked tests plus curl commands that can run from the
  maintenance host or deployment wrapper context.
- Keep V1 bounded: no escrow, conflict tracking expansion, geocoding, or vector
  search work in this slice.

## Implemented

- Added mocked bot smoke coverage in
  `telegram-bot/tests/test_handler_rental.py` for:
  - inline `/rent_search ...` execution with parsed date parameters and empty
    search feedback;
  - successful booking callback handoff, booking prompt registration, and owner
    notification;
  - successful payment-proof message handling, recipient notice, saved-pack
    forwarding through `/api/show_tgmsg_pack`, user feedback, and FSM cleanup.
- Captured repeatable runtime smoke commands below so future rental handoffs can
  verify the public read surfaces and optional write-path handoff without
  reading source code.

## Smoke Commands

Live-safe read-only checks:

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/search/?query=tent&number=1'
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/user/points/?rental=on&number=1'
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/offer/'
```

Expected results:

- rental search returns HTTP 200 with an `offers` array;
- rental map exposure returns HTTP 200 with a `points` array, possibly empty;
- rental offer lookup without `uuid`/`offer_id` returns the expected HTTP 404.

Optional write-path smoke checks require a throwaway owner/requester pair,
`TELEGRAM_BOT_TOKEN`, and an active test rental offer. Run them only when test
data side effects are acceptable.

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  -H 'Content-Type: application/json' \
  -d '{"tg_token":"'"$TELEGRAM_BOT_TOKEN"'","user_uuid":"'"$REQUESTER_UUID"'","offer_uuid":"'"$OFFER_UUID"'","date_from":"2026-07-01","date_to":"2026-07-02"}' \
  'https://api.doverabot.ru/api/rental/reservation/'
```

Save `reservation.id` from the response as `RESERVATION_ID`, then smoke the
payment-proof handoff:

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  -H 'Content-Type: application/json' \
  -d '{"tg_token":"'"$TELEGRAM_BOT_TOKEN"'","user_uuid":"'"$REQUESTER_UUID"'","reservation_id":"'"$RESERVATION_ID"'","tgdesc":{"message_id":1,"chat_id":1,"media_group_id":"","caption":"rental smoke proof","file_id":"","file_type":"text","uuid_pack":"00000000-0000-0000-0000-000000000005"}}' \
  'https://api.doverabot.ru/api/rental/reservation/payment_proof/'
```

Close the write-path smoke reservation:

```bash
curl -sS -w '\nHTTP_STATUS=%{http_code}\n' \
  -X PUT \
  -H 'Content-Type: application/json' \
  -d '{"tg_token":"'"$TELEGRAM_BOT_TOKEN"'","user_uuid":"'"$REQUESTER_UUID"'","reservation_id":"'"$RESERVATION_ID"'","action":"cancel"}' \
  'https://api.doverabot.ru/api/rental/reservation/'
```

For Telegram callback smoke, the source-level tests now pin the callback data
surfaces:

- `82~<offer_uuid>` for booking;
- `83~payment_reported~<reservation_id>` for payment-proof entry;
- `83~cancel~<reservation_id>`, `83~owner_accept~<reservation_id>`, and
  `83~owner_confirm~<reservation_id>` for reservation updates.

## Verification

Checks run:

- `python3 -m unittest discover telegram-bot/tests -p 'test_handler_rental.py'`
  -> 13 tests OK.
- `python3 -m unittest discover telegram-bot/tests` -> 71 tests OK.
- `python3 -m compileall telegram-bot` -> OK.
- `bash scripts/reindex.sh` -> OK; local CODE_INDEX pyramid rebuilt to 121
  files and 1470 symbols.
- `uv tool run --from graphifyy graphify update .` -> OK; code graph
  rebuilt with 4397 nodes, 8792 edges, and 441 communities.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/search/?query=tent&number=1'`
  -> HTTP 200, `{"offers":[]}`.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/user/points/?rental=on&number=1'`
  -> HTTP 200, empty `points` payload.
- `curl -sS -w '\nHTTP_STATUS=%{http_code}\n' 'https://api.doverabot.ru/api/rental/offer/'`
  -> expected HTTP 404 without `uuid`/`offer_id`.

## Operational Handoff

- Runtime source was not changed in this slice; no deploy is required.
- Commit source/docs after checks pass with message
  `doverabot-rental-v1-smoke-observability`.

## Follow-Up Basket

Next suggested `/new-go-slug`:
`doverabot-next-decision-refresh`
