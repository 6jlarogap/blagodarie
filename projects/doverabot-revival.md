# Doverabot Revival

## Active Threads

### Rental Offers

Architecture reference: [../references/2026-06-18-doverabot-rental-offers-architecture.md](../references/2026-06-18-doverabot-rental-offers-architecture.md)

Chain: [../references/doverabot-rental-offers-chain.md](../references/doverabot-rental-offers-chain.md)

Next-work baskets: [../references/2026-06-18-doverabot-rental-next-work-baskets-chain.md](../references/2026-06-18-doverabot-rental-next-work-baskets-chain.md)

Current decision:

- Build travel-equipment rental as a new `/rent` surface.
- Keep poll-style `/offer` and `/offer_multi` unchanged.
- V1 is listing, search, map exposure, contact, and payment handoff only.
- Do not add booking, escrow, reservation conflict tracking, geocoding, or vector search in V1.

Current implementation:

- Rental models, migration, API endpoints, map exposure, bot command wiring, media capture, and contact handoff were added on 2026-06-18.
- The implementation keeps `/offer` and `/offer_multi` on the existing poll flow.

Primary implementation areas:

- `app/users/models.py`
- `app/users/views.py`
- `app/users/urls.py`
- `telegram-bot/common.py`
- `telegram-bot/handler_rental.py`
- `telegram-bot/main.py`

## Doverabot Backlog Captured

- Move active FSM storage away from `MemoryStorage` before relying on long rental flows.
- Centralize callback payload parsing.
- Add handler tests around offers, callbacks, media packs, and command interruption.
- Fix duplicate callback function names and known bug backlog from the interaction map.
- Replace hard-coded bot links with `bot_data.username`.
- Improve user feedback on unauthorized or expired callbacks.

## Next Implementation Slice

Harden the rental flow before broad rollout: replace `MemoryStorage`, wire the real Organizm/Hermes transcript handoff, broaden aiogram handler tests, and decide whether deployed map UI needs a frontend change for rental markers.

Suggested `/new-go-slug`: `doverabot-rental-deploy-forward-booking-voice-taxonomy-reservation`.

Accepted next-session decisions:

- Deployment is part of the next goal.
- Rental media should be sent by Telegram offer-message copy/forward, not local media storage.
- Client-facing copied offer messages get an inline booking keyboard.
- Equipment taxonomy starts with English/Russian terms.
- The 10th reservation globally substitutes system-owner payment credentials and notifies the rental owner.
