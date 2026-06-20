# Doverabot Equipment Rental Trust Flow Plan

Date: 2026-06-20
Status: accepted business process and topology plan
Scope: equipment rental trust flow in Doverabot

## Core Decision

Doverabot keeps one public bot identity. Equipment rental is exposed as a modular `/rent` feature flow inside the same Doverabot, alongside `/offer`, `/meet`, `rod`, `/trust`, and `/thank`.

Internally, each feature may have separate routers, modules, service objects, API namespaces, state machines, tests, and operational ownership. Publicly, users should experience one Doverabot concierge with clear commands and feature boundaries, not a family of service bots by default.

Dedicated public service bots are a later exception only when the product has a specific reason to split the identity.

## Roles

- Equipment owner: creates and manages rental listings, receives booking intents, accepts or cancels requests, and confirms completed handoffs.
- Requester or renter: searches for equipment, sends booking intent, receives payment or contact handoff instructions, and leaves post-rental trust feedback.
- Doverabot concierge: guides both sides through listing, search, reservation intent, payment handoff, notifications, and post-rental prompts.
- Trust graph: supplies gratitude, trust, acquaintance, reputation, and explicit mistrust signals that affect visibility, ranking, badges, and exclusions.
- System or project owner: operates Doverabot and may receive explicitly disclosed system-owner payment handoffs under configured rental policies.

## Rental Flow

1. Profile and trust setup

   Users enter Doverabot through the existing profile and trust graph surfaces. `/trust` and `/thank` remain shared primitives for declaring trust, gratitude, and relationship context before or after a rental interaction.

2. Listing creation

   An equipment owner uses `/rent` or rental-specific actions to create a listing. The listing captures item text, description, availability, location or address text, price/payment notes, media, visibility, and owner contact/payment handoff data.

3. Trust-aware search

   A requester searches active listings through `/rent`. Text and structured filters find candidate items first. Trust graph data then affects visibility, badges, ranking, and explicit mistrust exclusion. Trust is a signal and safety layer, not the only retrieval mechanism.

4. Booking intent

   When the requester chooses an item, Doverabot creates or reuses a non-terminal reservation intent and starts the owner/requester runtime flow. This is still a non-escrow process: the bot records intent and coordinates the handoff, but it does not hold funds.

5. Payment handoff

   Doverabot shows the requester the applicable payment or donation instructions before payment is made. The handoff can use offer-specific payment text, owner profile banking details, or an explicitly disclosed system-owner recipient under the configured reservation sequence policy.

6. Owner and customer notifications

   The owner receives the reservation intent and requester context. The requester receives status changes from owner acceptance, payment reported, confirmation, or cancellation. Doverabot records auditable reservation events for each runtime action.

7. Post-rental trust actions

   After the rental completes or fails, Doverabot should prompt the participants to update shared trust primitives where appropriate: `/thank` for successful help, `/trust` for durable trust changes, and explicit mistrust where a future exclusion is warranted.

## Feature Boundaries

- `/rent` is the equipment rental product surface: listing, search, booking intent, payment/contact handoff, rental notifications, and rental-specific post-flow prompts.
- `/offer` and `/offer_multi` remain poll-style offers backed by the existing offer/poll behavior. Rental listings must not be folded into those commands.
- `/meet` remains the meetgame flow.
- `rod` remains the family graph flow.
- `/trust` and `/thank` remain shared trust-graph primitives. Rental may call attention to them, but it should not fork or duplicate the trust graph.

## Split-Bot Criteria

A separate public bot identity becomes reasonable only if one of these conditions becomes material:

- separate brand or audience that would make the Doverabot identity confusing;
- moderation, compliance, payment, or policy boundary that must be operationally isolated;
- traffic or reliability isolation that cannot be solved cleanly inside one bot runtime;
- a materially different user journey where shared commands and profile context harm clarity.

Until then, the default topology is one Doverabot with modular feature flows.

## Interfaces

This plan does not require code, API, schema, command, deployment, or frontend changes.

Existing commands and endpoints are referenced as current system facts. Future implementation slices may add or change internals, but this slice only documents the product and trust-flow boundary.

## V1 Assumptions

- Public topology: one Doverabot.
- First documented business scope: equipment rental trust flow.
- Payment remains a non-escrow handoff.
- Trust affects visibility, badges, ranking, and explicit mistrust exclusion.
- Search remains item-first, then trust-aware; trust is not the sole search source.
