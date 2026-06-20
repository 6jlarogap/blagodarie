# Doverabot Rental Go Rent Baskets Chain

Date: 2026-06-20
Status: accepted one-session-shot basket chain
Parent plan: [2026-06-20-doverabot-equipment-rental-trust-flow-plan.md](2026-06-20-doverabot-equipment-rental-trust-flow-plan.md)
Suggested `/new go` command: `/new go rent`
Suggested slug: `go-rent`

## Chain Purpose

Implement the next equipment-rental trust flow slice inside the existing Doverabot `/rent` surface.

The goal is to make rental booking behave like a trusted payment-proof handoff:

- one active timed reservation hold per equipment/date interval;
- payment credentials shown only after trust and availability checks pass;
- payer sends payment proof in Telegram;
- proof is stored and forwarded through the existing Telegram media-pack mechanics;
- explicit mistrust blocks visibility and booking;
- voice-only listing and search conversations are supported;
- rental points become useful in the existing map UX.

This chain should keep Doverabot as one public bot identity. It must not create a separate rental bot.

## Basket: Documentation Alignment

Problem:

- `2026-06-18-doverabot-rental-offers-architecture.md` originally says V1 must not implement booking or reservations.
- Later chains implemented `RentalReservationIntent`, `RentalReservationEvent`, reservation actions, booking keyboards, and runtime owner/requester notifications.

Accepted change:

- Add a superseding note to the older architecture document that reservation runtime behavior is now governed by the runtime chain and this `go-rent` basket chain.
- Keep `/offer` and `/offer_multi` poll behavior separate from rental.
- Keep `/rent` as the equipment rental surface.

## Basket: Timed Reservation Hold And Concurrency

Accepted business rule:

- A reservation hold is created immediately when the requester taps Reserve, after trust and availability checks pass.
- For V1, use a 10 minute payment-proof hold.
- Only one non-expired active hold or booked reservation may exist for the same equipment/date interval.
- If payment proof is not received before the hold expires, the hold is cancelled or expired and the equipment/date interval becomes available again.
- Payment after expiration does not guarantee booking.

Implementation direction:

- Add reservation statuses such as `awaiting_payment`, `payment_proof_submitted`, `confirmed`, `cancelled`, and `expired`, or map the same semantics onto the existing statuses if that is less invasive.
- Store `hold_expires_at` on the reservation.
- Require structured dates before showing payment credentials for a real booking. If dates are missing, keep the flow as contact/request clarification.
- Use a PostgreSQL transaction and row lock around reservation creation and proof submission.
- For V1, lock the `RentalOffer` row with `select_for_update()` and check overlapping active reservations inside the same transaction.
- Later, consider a PostgreSQL date-range exclusion constraint if interval overlap logic becomes more complex.

Blocking statuses for overlap:

- `awaiting_payment` until `hold_expires_at`;
- `payment_proof_submitted`;
- `confirmed`.

## Basket: Trust Visibility And Booking Exclusion

Accepted rule:

- Explicit mistrust in either direction between requester and owner is a hard exclusion.
- A requester who has explicit mistrust from the owner, or who explicitly mistrusts the owner, must not see that owner's rental offers in search or map results.
- The booking API must also reject such reservations server-side.

Trust remains a signal for ranking and badges, but explicit mistrust is a safety boundary.

Implementation direction:

- Apply the same mistrust exclusion in rental search, rental map points, rental offer fetch when used for booking, and reservation creation.
- Keep trust/acquaintance/reputation badges visible on allowed results.
- Do not rely only on frontend hiding or bot search filtering.

## Basket: Payment-Proof Subsystem Reuse

Accepted rule:

- Reuse the existing Doverabot payment/donation proof subsystem pattern.
- Do not force rental proof into `/api/thank_bank` if that would attach rental proof to `Journal` instead of the rental reservation audit trail.

Reuse these existing mechanics:

- payment credentials from profile banking details or offer-specific payment text;
- `TgDesc.from_message` for proof screenshots, photos, videos, voice, documents, and comments;
- `uuid_pack` grouping for media packs;
- `/api/show_tgmsg_pack` for forwarding saved proof packs to Telegram recipients;
- bot UX pattern: show credentials, wait for proof, forward proof, notify payer and recipient.

Rental-specific implementation:

- Add a rental payment-proof API, for example `POST /api/rental/reservation/payment_proof`.
- Store proof media against the reservation audit trail, preferably on the payment-proof event or on a small `RentalReservationPaymentProof` model linked to `RentalReservationIntent`.
- Record the proof sender, reservation, `uuid_pack`, original Telegram message identity, recipient kind, and timestamp.
- On proof receipt, re-check availability and trust in a transaction before marking the reservation as booked.

## Basket: Owner Recipient Flow

Normal owner-recipient flow:

1. Requester taps Reserve.
2. Bot creates a 10 minute hold.
3. Bot shows owner payment credentials.
4. Requester sends payment proof.
5. Proof is stored and forwarded to the owner.
6. Reservation becomes booked under proof.
7. Owner approves/handles equipment handoff and confirms final status.
8. If proof is fake or unacceptable, owner may reject/cancel and use mistrust when warranted.

For owner-recipient reservations, the owner can verify payment because the owner receives the money.

## Basket: 10th/System Recipient Trust-First Flow

Accepted business rule:

- Every configured 10th reservation may use system-owner payment credentials.
- The requester must see, before paying, that this reservation's payment goes to the system owner for Doverabot support.
- The equipment owner must also see that this is the 10th/system-recipient reservation.
- The system owner must not become a conveyor bottleneck for booking approval.

Trust-first flow:

1. Requester taps Reserve.
2. Bot creates a 10 minute hold after trust and availability checks.
3. Bot shows system-owner payment credentials and explains why.
4. Requester sends proof.
5. Proof submission books the equipment under trust if the hold is still valid and no conflict appeared.
6. Bot forwards proof to the equipment owner for awareness and to the system owner for audit.
7. Equipment owner proceeds with handoff and confirms final status.
8. System owner may audit later. If proof is fake, record an audit-failed event and allow mistrust/moderation consequences.

Important wording:

- Do not say "payment verified" for system-recipient reservations unless the system owner actually verified it.
- Say "proof received; reservation booked under trust."

## Basket: Voice-Only Listing Flow

Accepted rule:

- Owners should be able to create rental listings by voice-only conversation.
- The bot should ask concise follow-up questions only for missing or unclear fields.

Fields to collect:

- equipment type;
- model or brand;
- size;
- place, address, Telegram location, or coordinates;
- available dates;
- price and payment terms;
- useful media or photo.

Implementation direction:

- Lock the real Hermes/Organizm STT contract before broad work.
- Move long rental FSM state away from volatile `MemoryStorage` before depending on multi-step voice conversations.
- Use voice transcript slot extraction first, then clarification prompts.
- Ambiguous equipment terms such as `board` or `doska` should ask a clarification instead of guessing.
- Start with English/Russian equipment vocabulary.

## Basket: Voice-Only Search Flow

Accepted rule:

- Requesters should be able to search by voice-only conversation.
- The bot should ask for missing search constraints and then propose selectable options.

Search prompts:

- equipment type;
- model or size when relevant;
- place/address/location;
- dates;
- price constraints if useful.

Result UX:

- show ranked options with trust badges;
- each option should have Details, Reserve, Contact, and Show on map actions when available;
- if the listing has no coordinates, show it in list results but not as a map marker;
- if map filtering is requested and location is missing, ask for Telegram location or coordinates.

## Basket: Existing Map UX Improvements

Accepted rule:

- Improve and reuse the existing map/frontend path for rental offers.
- Do not build a separate rental map product unless the existing map cannot support the needed UX.

UX improvements:

- rental-specific marker icon or color distinct from people, meet, and poll offers;
- filters for equipment type, dates, price, trusted-only, and nearby;
- marker popup with title, price, availability dates, owner trust badge, and actions;
- `Open in bot` or deep link from map marker to the rental listing;
- `Show on map` action from bot search results;
- consistent mistrust hiding between bot search, backend API, and map frontend;
- no marker leak for private or hidden listings.

Implementation direction:

- Extend existing rental map points from `/api/user/points?rental=on` or `with_rentals=on`.
- Update the frontend map source if required for rental marker/filter visibility.
- Keep generated `frontend/*/dist/` untouched unless the deployment slice explicitly requires rebuilding deployed assets.

## Basket: Tests And Verification

Backend checks:

- `cd app && ./manage.py check`
- focused tests for timed hold creation, expiration, overlap rejection, proof submission, mistrust exclusion, owner-recipient proof, and system-recipient proof.
- migration dry-run with `cd app && ./manage.py makemigrations --check --dry-run`

Bot checks:

- `python -m compileall telegram-bot`
- mocked handler tests for Reserve, proof capture, media-pack forwarding, timeout messaging, voice listing, voice search, and map links.

Map/API checks:

- rental points appear only when visibility, trust, dates, and coordinates allow;
- explicit mistrust hides points and rejects booking;
- private listings do not leak.

Operational handoff:

- If runtime code or migrations change, commit with message `go-rent`.
- Deploy through the `blagodarie-admin` wrapper after checks pass.
- Run deploy/status/log checks.
- Record successful verification or exact blockers in `log.md` or this chain reference.

## Handoff Result, 2026-06-20

Implemented and committed:

- `2a6d030 go-rent`: timed rental holds, payment-proof API/storage, trust and overlap enforcement, bot proof capture/forwarding, map rental filters/marker metadata, focused tests, and docs alignment.
- `b40c750 go-rent deploy excludes`: source update to keep local agent/graph artifacts out of wrapper rsync deploys.

Checks run:

- `python3 -m py_compile app/users/models.py app/users/views.py app/users/tests.py app/users/migrations/0060_rentalreservation_hold_paymentproof.py telegram-bot/handler_rental.py telegram-bot/common.py` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py check` from `app/` -> OK.
- `/srv/blagodarie/venv-app/bin/python manage.py makemigrations --check --dry-run` from `app/` -> "No changes detected"; sandbox emitted PostgreSQL socket warning: `Operation not permitted`.
- `python3 -m compileall telegram-bot` -> OK.
- `uv tool run --from graphifyy graphify update .` -> OK, graph rebuilt.
- `sudo -n /usr/local/sbin/blagodarie-admin check-django` -> completed with existing deploy warning `security.W002`.
- `sudo -n /usr/local/sbin/blagodarie-admin is-active` -> nginx, web, and bot all `active`.

Blocked checks/deploy:

- Focused Django tests are blocked by local PostgreSQL peer auth. Command: `/srv/blagodarie/venv-app/bin/python manage.py test users.tests.ApiRentalOfferTests`. Result, both sandboxed and unsandboxed: `FATAL: Peer authentication failed for user "postgres"`.
- Live deploy was not run. `sudo -n /usr/local/sbin/blagodarie-admin deploy-dry-run` showed the installed wrapper would sync local non-runtime artifacts including `.codex/`, `graphify-out/`, dirty `log.md`, and `scripts/graphify-code.sh`.
- The source wrapper now excludes those artifacts, but installing it is blocked by sudo authentication. Commands tried:
  - `sudo bash deploy/install-blagodarie-admin-workflow.sh` -> `sudo: A terminal is required to authenticate`
  - `sudo -n bash deploy/install-blagodarie-admin-workflow.sh` -> `sudo: interactive authentication is required`

Next operator step: install the updated wrapper or otherwise deploy from a clean workspace, then run `sudo -n /usr/local/sbin/blagodarie-admin migrate`, `deploy`, `is-active`, and rental API smoke checks.

## Out Of Scope

- Escrow or in-bot payment processing.
- Separate public rental bot identity.
- Recursive live trust-depth filtering for every search request.
- Vector search as the source of truth for equipment matching.
- Full inventory quantity management beyond one listing as one rentable item.

## Open Follow-Up Decisions

- Whether one listing can later represent multiple identical inventory items.
- Whether fake-proof audit failures should auto-create mistrust or only prompt involved users.
- Whether hold duration should remain 10 minutes or become configurable per owner/listing.
