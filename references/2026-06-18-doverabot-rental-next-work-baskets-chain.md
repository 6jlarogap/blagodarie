# Doverabot Rental Next Work Baskets Chain

Date: 2026-06-18
Status: accepted one-session-shot basket chain
Parent chain: [doverabot-rental-offers-chain.md](doverabot-rental-offers-chain.md)
Suggested `/new-go-slug`: `doverabot-rental-deploy-forward-booking-voice-taxonomy-reservation`

## Basket: Deploy And Smoke Test

The current rental implementation is not considered deployed until the changed files are committed, migrations are applied, services are restarted, and smoke tests pass. Deployment belongs inside the next `/new-go-slug` session, not this closing session.

Deployment checklist:

- Run backend checks in the production app environment.
- Run migration plan and apply `users.0058_rentaloffer_rentaloffercontactrequest`.
- Restart API and bot through the deployment wrapper.
- Smoke test `/api/rental/offer`, `/api/rental/search`, `/api/user/points?rental=on`, `/rent`, `/rent_offer`, and `/rent_search`.
- Verify legacy `/offer` and `/offer_multi` still create poll offers.

Accepted decision:

- Chain deployment into the next one-session-shot goal.
- Start that goal by running checks in the production app/bot environments, then deploy only if the checks pass.

Follow-up handover go-next-slug: `doverabot-rental-deploy-forward-booking-voice-taxonomy-reservation`.

## Basket: Telegram Message Identity, Forwarding, And Booking Keyboard

Current implementation:

- Rental media metadata is stored through `TgDesc`, including `chat_id`, `message_id`, `media_group_id`, `caption`, `file_id`, `file_type`, and `uuid_pack`.
- This does not store local media files.
- It does not yet store a canonical "published rental offer message id" for each rendered listing sent by the bot.

Accepted change:

- Do not build a local rental media storage flow.
- Store only the canonical Telegram offer message identity needed to copy/forward the offer message.
- Add an inline booking keyboard to the client-facing copied offer message, similar to `/offer`, `/offer_multi`, and the `/meet` on-demand profile forwarding flow.

Recommended next model:

- `RentalOfferMessage`
  - `offer`
  - `chat_id`
  - `message_id`
  - `message_kind`: owner_offer, search_result, booking_prompt, contact_handoff
  - `recipient`
  - `insert_timestamp`

Forwarding rule:

- Prefer Telegram `copy_message` of the canonical owner offer message with `reply_markup` for the booking keyboard.
- If raw `forward_message` is required, send the booking keyboard as a separate follow-up message, because raw forwards do not provide the same keyboard attachment behavior.
- Store outbound `message_id` when a copied offer/search result/booking prompt is sent, so callbacks can reference the exact bot-rendered message.

Booking callback:

- Inline button: "Book" or "Reserve".
- Callback creates or updates `RentalReservationIntent`.
- Callback then sends the appropriate payment credentials for this reservation sequence.

Follow-up handover go-next-slug: `doverabot-rental-deploy-forward-booking-voice-taxonomy-reservation`.

## Basket: Voice-Only Managed Search

Goal:

- Bot asks in text: what equipment is needed, when, and where.
- User can answer only by voice.
- Bot converts voice to transcript through the existing Organizm/Hermes STT pipeline, extracts slots, and asks only missing clarifying questions.

Required flow:

1. `/rent_search` enters a rental search FSM state.
2. Bot sends a broad text prompt.
3. User replies with voice.
4. Bot sends Telegram `file_id` or downloaded audio bytes to the existing STT service, depending on the Hermes contract.
5. Bot receives transcript.
6. Slot extraction fills item, date/time, address/coordinate text.
7. If the location is typed or spoken, store it as address text; ask for Telegram location or coordinates when map filtering is needed.
8. Search runs when item and at least one usable location/date clue exists.
9. If confidence is low, bot asks a short follow-up question.

Minimal backend support:

- Optional `RentalSearchSession` model for audit/debug if search sessions must survive bot restart.
- Otherwise keep it in durable bot FSM storage once `MemoryStorage` is replaced.

Decision needed:

- Hermes STT contract: should Doverabot send a Telegram `file_id`, download bytes and upload them, or receive a transcript pushed from Organizm?

Accepted scope:

- Discover the actual Hermes STT contract during the next one-session-shot goal and implement the matching adapter in that same goal if the contract is locally available.

Follow-up handover go-next-slug: `doverabot-rental-deploy-forward-booking-voice-taxonomy-reservation`.

## Basket: Equipment Tags And Multilingual Matching

Problem examples:

- snowboard
- board
- splitboard
- сноуборд
- доска
- сплитборд

Recommended V1:

- Add `RentalEquipmentType`
  - `slug`
  - `parent`
  - `canonical_name`
  - `labels`: per-language display names
  - `synonyms`: per-language synonyms
  - `is_ambiguous`
- Add a many-to-many or nullable FK from `RentalOffer` to equipment types.
- During listing creation and search, tag equipment with confidence.
- If a term is ambiguous, ask a clarification instead of guessing.

Matching stack:

- Use curated synonym tables first.
- Use PostgreSQL full-text search plus trigram similarity and optional `unaccent`.
- Keep vector search as a later semantic-search basket after curated tags exist.

Examples:

- `snowboard`, `сноуборд` -> `snowboard`
- `splitboard`, `сплитборд` -> `splitboard`, child of `snowboard`
- `board`, `доска` -> ambiguous; ask whether this means snowboard, surfboard, SUP board, longboard, or another board.

Decision needed:

- Start with English/Russian equipment vocabulary only, or include more languages immediately.

Accepted decision:

- Start with English/Russian equipment vocabulary.
- Keep ambiguous terms such as `board` and `доска` as clarification prompts, not automatic matches.

Follow-up handover go-next-slug: `doverabot-rental-deploy-forward-booking-voice-taxonomy-reservation`.

## Basket: Reservation Donation And Payment Handoff

Current V1:

- No booking, escrow, reservation conflict tracking, or in-bot payment processing.
- Payment info is only a handoff: offer-specific payment text first, profile banking details as fallback.

Proposed next step:

- Add a non-escrow `RentalReservationIntent`.
  - `offer`
  - `requester`
  - `date_from`, `date_to`
  - `amount_suggested`
  - `currency`
  - `recipient_kind`: owner or system
  - `recipient_payment_info_snapshot`
  - `sequence_number`
  - `status`: draft, sent, owner_accepted, payment_reported, confirmed, cancelled

Important rule:

- Any system-owner donation must be explicit before the user pays. The bot should say who receives the money and why.

Accepted 10th-donation mechanics:

- Use a global 10th-reservation counter first.
- On each 10th reservation, substitute rental-owner payment credentials with system-owner payment credentials.
- Show the client that this reservation's donation goes to the system owner for project improvement.
- Send a notification copy to the rental owner so the owner knows the reservation is done and the client is a trustable, payable person.
- No escrow is added. This remains a direct p2p donation/payment handoff.

Implementation notes:

- Store `recipient_kind`: `owner` or `system`.
- Store `recipient_payment_info_snapshot` at intent creation time, so later profile edits do not rewrite historical reservation instructions.
- Store and display the global reservation sequence number.
- Owner notification must include the offer, requester profile, selected dates if present, amount, recipient kind, and payment-info recipient shown to the requester.

Follow-up handover go-next-slug: `doverabot-rental-deploy-forward-booking-voice-taxonomy-reservation`.

## Basket: `/new-go-slug`

Suggested slug:

`doverabot-rental-deploy-forward-booking-voice-taxonomy-reservation`

Use this slug when starting the next implementation goal after the pending decisions are answered. The basket should include:

- deployment decision
- deployment checks and deploy if green
- Telegram message identity model with copied/forwarded offer message behavior
- inline booking keyboard
- voice-only search STT contract
- English/Russian equipment taxonomy seed
- global 10th reservation system-owner payment substitution
