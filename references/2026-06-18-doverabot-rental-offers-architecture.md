# Doverabot Rental Offers Architecture

Date: 2026-06-18
Status: accepted architecture; initial V1 code slice implemented on 2026-06-18
Scope: travel-equipment rental listings in Doverabot

## Decision

Travel-equipment rental must be a new rental surface, not a reuse of the existing poll-style `/offer` flow. The current `/offer` and `/offer_multi` behavior is backed by `Offer`, `OfferAnswer`, and poll-specific bot callbacks, so it should remain unchanged.

V1 is listing, search, map exposure, contact, and payment handoff only. It must not implement booking, escrow, reservations, or conflict tracking.

Superseding note, 2026-06-20: reservation runtime behavior is now governed by
`2026-06-18-doverabot-rental-runtime-concierge-owner-consumer-agent-chain.md`
and `2026-06-20-doverabot-rental-go-rent-baskets-chain.md`. `/offer` and
`/offer_multi` remain poll surfaces; `/rent` is the equipment rental surface.
Escrow and in-bot payment processing remain out of scope.

## Command Surface

Add rental-specific bot commands:

- `/rent` opens a rental hub with create, search, and own-listings actions.
- `/rent_offer` starts listing creation.
- `/rent_search` starts equipment search.

Keep the current poll commands unchanged:

- `/offer`
- `/offer_multi`

Recommended bot placement:

- Put rental handlers in a new `telegram-bot/handler_rental.py` module.
- Reuse shared helpers from `telegram-bot/common.py`.
- Do not add rental branches to poll-only callback handling unless the callback payload is first made explicit and centralized.

## Backend Data Model

Add rental-specific models near the existing offer/profile/`TgDesc` models in `app/users/models.py`.

`RentalOffer`:

- `owner`: `auth.User` foreign key.
- `uuid`: stable public identifier.
- `status`: draft, active, paused, archived.
- `title`: short item title.
- `item_text`: normalized item/category text when extraction can identify it.
- `description_text`: owner-provided details and voice transcript summary.
- `price_text`: human-readable price and payment note.
- `price_amount`, `price_currency`, `price_period`: optional structured price fields.
- `availability_text`: free-form availability note.
- `available_from`, `available_to`: optional date filters.
- `visibility`: authenticated users, trusted-environment listing, or private-link only.
- `latitude`, `longitude`, `address`: same geodata shape as `GeoPointAddressModel`.
- `tgdesc`: media descriptions using `TgDesc`.
- insert/update timestamps.

`RentalOfferContactRequest`:

- `requester`: `auth.User` foreign key.
- `offer`: `RentalOffer` foreign key.
- `message`: requester text.
- `transcript`: voice-derived text when applicable.
- insert timestamp.

Payment details:

- Store offer-specific payment text when supplied.
- When blank, reuse the owner's profile banking details as the display/handoff source.
- Do not store escrow state in V1.

## API Surface

Add rental endpoints beside the current offer endpoints in `app/users/views.py` and `app/users/urls.py`.

Required:

- `POST /api/rental/offer`: create a rental listing.
- `GET /api/rental/offer`: fetch one listing by `uuid` or internal id.
- `PUT /api/rental/offer`: update owner-controlled fields, status, location, and media.
- `GET /api/rental/search`: search active visible listings.

Optional V1 handoff:

- `POST /api/rental/contact`: create `RentalOfferContactRequest` and notify or expose owner contact flow.

Authorization:

- Bot write endpoints use the same bot token boundary as existing bot-facing APIs.
- Owner-only updates must check the authenticated or Telegram-linked owner.
- Public search must never expose private-link-only listings unless searched by an explicit private token/link contract added later.

## Media And Voice

Reuse `TgDesc` for rental media so photo, video, document, audio, and voice metadata can be preserved. Extend the bot-side `TgDesc.from_message` to recognize voice messages in addition to the existing photo/audio/video/document handling.

Voice UX is hybrid:

- Ask one broad question first: what item, where, when, price, and important details.
- Accept text or voice.
- STT is delegated to the existing Organizm/Hermes STT pipeline.
- Doverabot receives transcript text and performs slot extraction plus confirmation.
- Ask follow-up questions only for missing or low-confidence fields.

No Whisper or other STT runtime is added inside Doverabot for V1.

## Address And Location

Reliable coordinate paths:

- Telegram location message.
- Typed coordinates accepted by existing coordinate parsing rules.

Free-form address handling:

- Store spoken or typed address text immediately.
- Do not invent address-to-coordinate geocoding in V1.
- Show address variants only after a geocoding provider and contract are explicitly added.

## Search

Use PostgreSQL full-text search over listing fields:

- title
- item/category text
- description text
- address/location text

Filters:

- active status
- date availability when structured dates exist
- coordinate bounding box or distance when coordinates exist
- visibility rules
- explicit mistrust exclusions

Ranking:

- Text relevance first.
- Use trust, acquaintance, and reputation signals for ranking boosts and badges.
- Do not make trust the only retrieval mechanism.

Defer vector search to a later semantic-search milestone. It can help item-text matching, but it must not become the source of truth for trust graph membership.

## Map

Extend `ApiUserPoints` in `app/users/views.py` with rental map support:

- `rental=on`: expose rental offers as map points.
- `with_rentals=on`: include rental points alongside user/profile points when appropriate.

Behavior should mirror existing offer point handling while using rental visibility rules. Only active listings with coordinates should become points. Private and hidden listings must not leak through the map endpoint.

## Trust And Privacy

Visibility choices:

- authenticated Doverabot users
- trusted-environment listing
- private-link only

V1 does not run recursive trust-depth filtering for every search request.

Always:

- hide explicit mistrust conflicts
- show trust/acquaintance/reputation badges
- keep owner contact details behind the contact handoff until the chosen visibility/contact rules allow exposure

Follow-up:

- Add materialized trust-network ids if exact long-chain network membership is required without recursive live queries.

## Non-Goals For V1

- Booking calendar.
- Reservation conflict detection.
- Escrow.
- In-bot payments.
- Geocoding provider integration.
- Vector database.
- Recursive live trust-depth search filtering.

## Doverabot Follow-Ups Captured

- Move active FSM storage away from `MemoryStorage` before relying on long rental flows.
- Centralize callback payload parsing.
- Add handler tests around offers, callbacks, media packs, and command interruption.
- Fix duplicate callback function names and known backlog from the interaction map.
- Replace hard-coded bot links with `bot_data.username`.
- Improve user feedback on unauthorized or expired callbacks.

## Test Plan

Backend:

- `cd app && ./manage.py check`
- focused model/API tests for rental offer create/get/update/search/contact
- migration dry-run with `./manage.py makemigrations --check --dry-run`

Bot:

- `python -m compileall telegram-bot`
- mocked aiogram tests for `/rent_offer`, `/rent_search`, voice transcript slot-fill, media description save, contact handoff, and legacy `/offer` regression

Map/API:

- rental points appear when coordinates and visibility allow them
- hidden/private offers do not leak
- explicit mistrust exclusions apply

Search:

- text and voice-derived queries match item/date/location combinations
- missing fields trigger clarification rather than low-quality listings

## Implementation Notes

Recommended implementation order:

1. Add models and migrations.
2. Add API endpoints and focused backend tests.
3. Add rental bot handlers and callback payload constants.
4. Add voice transcript slot extraction and media save support.
5. Extend map/search behavior.
6. Harden FSM storage and callback parsing before broad rollout.

Open assumptions:

- New rental commands are accepted over changing `/offer`.
- V1 remains listing/search/contact only.
- Map integration is required.
- Generated frontend bundles remain untouched unless a later task explicitly targets deployed map UI.

Initial code slice completed on 2026-06-18:

- Added rental models and migration.
- Added rental offer, search, and contact APIs.
- Added rental map exposure through `ApiUserPoints`.
- Added `/rent`, `/rent_offer`, `/rent_search`, rental deep links, media save, and contact handoff in the bot.
- Added focused backend tests for create/search visibility.
