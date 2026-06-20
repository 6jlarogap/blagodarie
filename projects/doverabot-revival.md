# Doverabot Revival

## Active Threads

### Rental Offers

Architecture reference: [../references/2026-06-18-doverabot-rental-offers-architecture.md](../references/2026-06-18-doverabot-rental-offers-architecture.md)

Chain: [../references/doverabot-rental-offers-chain.md](../references/doverabot-rental-offers-chain.md)

Next-work baskets: [../references/2026-06-18-doverabot-rental-next-work-baskets-chain.md](../references/2026-06-18-doverabot-rental-next-work-baskets-chain.md)

Runtime concierge chain: [../references/2026-06-18-doverabot-rental-runtime-concierge-owner-consumer-agent-chain.md](../references/2026-06-18-doverabot-rental-runtime-concierge-owner-consumer-agent-chain.md)

Business process and topology plan: [../references/2026-06-20-doverabot-equipment-rental-trust-flow-plan.md](../references/2026-06-20-doverabot-equipment-rental-trust-flow-plan.md)

Current decision:

- Keep one public Doverabot identity with modular feature flows: `/rent`, `/offer`, `/meet`, `rod`, `/trust`, and `/thank`.
- Build travel-equipment rental as a new `/rent` surface.
- Keep poll-style `/offer` and `/offer_multi` unchanged.
- V1 is listing, search, map exposure, contact, reservation intent, and payment handoff only.
- Do not add escrow, reservation conflict tracking, geocoding, or vector search in V1.
- Treat dedicated public service bots as a future exception only for separate branding, moderation/compliance boundaries, traffic isolation, or a materially different user journey.

Current implementation:

- Rental models, migration, API endpoints, map exposure, bot command wiring, media capture, and contact handoff were added on 2026-06-18.
- The implementation keeps `/offer` and `/offer_multi` on the existing poll flow.
- Rental reservation runtime now has owner/consumer bot callbacks for accept, payment reported, confirm, and cancel, with audited backend events.
- The rental trust-flow business process is documented as a docs-only reference on 2026-06-20.

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

Harden the rental flow before broad rollout: replace `MemoryStorage`, verify the real Organizm/Hermes transcript handoff, broaden aiogram handler tests, and decide whether deployed map UI needs a frontend change for rental markers.

Suggested `/new-go-slug`: `doverabot-rental-durable-fsm-hermes-map-marker-tests`.

Accepted prior-session decisions:

- Deployment is part of the next goal.
- Rental media should be sent by Telegram offer-message copy/forward, not local media storage.
- Client-facing copied offer messages get an inline booking keyboard.
- Equipment taxonomy starts with English/Russian terms.
- The 10th reservation globally substitutes system-owner payment credentials and notifies the rental owner.
