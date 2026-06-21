# Doverabot Revival

## Active Threads

### Rental Offers

Architecture reference: [../references/2026-06-18-doverabot-rental-offers-architecture.md](../references/2026-06-18-doverabot-rental-offers-architecture.md)

Chain: [../references/doverabot-rental-offers-chain.md](../references/doverabot-rental-offers-chain.md)

Next-work baskets: [../references/2026-06-18-doverabot-rental-next-work-baskets-chain.md](../references/2026-06-18-doverabot-rental-next-work-baskets-chain.md)

Runtime concierge chain: [../references/2026-06-18-doverabot-rental-runtime-concierge-owner-consumer-agent-chain.md](../references/2026-06-18-doverabot-rental-runtime-concierge-owner-consumer-agent-chain.md)

Business process and topology plan: [../references/2026-06-20-doverabot-equipment-rental-trust-flow-plan.md](../references/2026-06-20-doverabot-equipment-rental-trust-flow-plan.md)

Callback hardening chain: [../references/2026-06-21-doverabot-rental-callback-payload-feedback-chain.md](../references/2026-06-21-doverabot-rental-callback-payload-feedback-chain.md)

Runtime bot link cleanup chain: [../references/2026-06-21-doverabot-runtime-bot-link-cleanup-chain.md](../references/2026-06-21-doverabot-runtime-bot-link-cleanup-chain.md)

Profile-edit callback feedback finish chain: [../references/2026-06-21-doverabot-profile-edit-callback-feedback-finish-chain.md](../references/2026-06-21-doverabot-profile-edit-callback-feedback-finish-chain.md)

Profile-edit state feedback finish chain: [../references/2026-06-21-doverabot-profile-edit-state-feedback-finish-chain.md](../references/2026-06-21-doverabot-profile-edit-state-feedback-finish-chain.md)

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
- Durable Redis-backed FSM storage, explicit Organizm/Hermes STT handoff helpers, and deployed rental map marker forwarding were completed on 2026-06-21.
- Rental booking/contact/reservation callbacks now have centralized payload parsing and user-visible stale/auth failure feedback.
- The remaining runtime hard-coded Doverabot deep link in the sympathy contact handoff now uses the live bot username helper.
- Profile-edit callbacks in `handler_callbacks.py` no longer use direct `callback.data.split(KeyboardType.SEP)` parsing, and the edited stale/auth exits now use shared visible callback notices.
- Remaining parser-backed profile-edit callback failure exits now return visible stale/auth notices across IOF, DOB unknown, comments, delete/undelete, messaging/archive, user description, banking, meet edit-back, and archive deletion.
- Profile-edit message-state handlers now give visible feedback for stale FSM data, profile auth failure, and API failure across IOF, meet DOB/description, date/comment/message/user-desc/banking, and thank-bank states.

Primary implementation areas:

- `app/users/models.py`
- `app/users/views.py`
- `app/users/urls.py`
- `telegram-bot/common.py`
- `telegram-bot/handler_rental.py`
- `telegram-bot/main.py`

## Doverabot Backlog Captured

- Centralize remaining non-rental callback payload parsing.
- Add handler tests around offers, callbacks, media packs, and command interruption.
- Fix duplicate callback function names and known bug backlog from the interaction map.
- Keep hard-coded bot/deep-link cleanup enforced in newly touched bot flows.
- Improve user feedback on unauthorized or expired callbacks.

## Next Implementation Slice

No immediate next `/new-go-slug` is selected after `doverabot-profile-edit-state-feedback-finish`.

Remaining backlog stays focused on callback/parser cleanup, handler coverage, duplicate handler names, and bot/deep-link consistency in newly touched flows.

Accepted prior-session decisions:

- Deployment is part of the next goal.
- Rental media should be sent by Telegram offer-message copy/forward, not local media storage.
- Client-facing copied offer messages get an inline booking keyboard.
- Equipment taxonomy starts with English/Russian terms.
- The 10th reservation globally substitutes system-owner payment credentials and notifies the rental owner.
