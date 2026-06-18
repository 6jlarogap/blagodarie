# doverabot-rental-offers-chain

Status: active architecture chain
Root reference: [2026-06-18-doverabot-rental-offers-architecture.md](2026-06-18-doverabot-rental-offers-architecture.md)
Next baskets: [2026-06-18-doverabot-rental-next-work-baskets-chain.md](2026-06-18-doverabot-rental-next-work-baskets-chain.md)
Runtime concierge chain: [2026-06-18-doverabot-rental-runtime-concierge-owner-consumer-agent-chain.md](2026-06-18-doverabot-rental-runtime-concierge-owner-consumer-agent-chain.md)

## Chain Purpose

Track the Doverabot rental-offers feature as a distinct product and engineering thread. The chain exists to keep rental implementation decisions separate from the existing poll-style `/offer` surface.

## Child: Data Model And API

Reference sections:

- Backend Data Model
- API Surface
- Non-Goals For V1

Implementation targets:

- `app/users/models.py`
- `app/users/views.py`
- `app/users/urls.py`
- `app/users/migrations/`

Acceptance notes:

- `RentalOffer` and `RentalOfferContactRequest` exist independently from `Offer` and `OfferAnswer`.
- `POST/GET/PUT /api/rental/offer` and `GET /api/rental/search` are covered by focused tests.
- Optional `POST /api/rental/contact` stores contact handoff requests without creating booking state.

## Child: Bot Voice UX

Reference sections:

- Command Surface
- Media And Voice
- Address And Location

Implementation targets:

- `telegram-bot/handler_rental.py`
- `telegram-bot/common.py`
- `telegram-bot/main.py`

Acceptance notes:

- `/rent`, `/rent_offer`, and `/rent_search` are registered.
- `/offer` and `/offer_multi` still behave as poll commands.
- Voice transcript text can fill rental slots after external STT returns a transcript.
- Follow-up prompts are only used for missing or uncertain fields.

## Child: Search And Map

Reference sections:

- Search
- Map
- Address And Location

Implementation targets:

- `app/users/views.py`
- `app/users/models.py`
- map endpoint consumers only when explicitly requested

Acceptance notes:

- Search uses PostgreSQL full-text search plus structured filters.
- Rental map points are exposed through `ApiUserPoints` with `rental=on` and `with_rentals=on`.
- Listings without coordinates can still be searched but do not appear as map points.

## Child: Trust And Privacy

Reference sections:

- Trust And Privacy
- Search
- Map

Implementation targets:

- visibility filtering in rental APIs
- explicit mistrust exclusion checks
- badge data returned with search/listing payloads

Acceptance notes:

- Private-link-only listings do not appear in public search or map responses.
- Explicit mistrust conflicts are hidden.
- Trust, acquaintance, and reputation are shown as badges/ranking signals, not used as the only search gate.

## Child: Tests

Reference sections:

- Test Plan
- Doverabot Follow-Ups Captured

Implementation targets:

- backend API/model tests
- bot handler tests with mocked aiogram messages/callbacks
- regression tests for legacy offer behavior

Acceptance notes:

- `cd app && ./manage.py check` passes.
- `cd app && ./manage.py makemigrations --check --dry-run` passes after schema work is complete.
- `python -m compileall telegram-bot` passes.
- Tests cover media packs, voice transcript slot-fill, command interruption, unauthorized callbacks, and legacy `/offer` regression.
