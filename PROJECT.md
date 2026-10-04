# Qriously

## What it is

A learning platform. This project is its homepage — the first thing a visitor
sees, and the moment that has to make them feel curious.

## The page

One screen, centered, dark and glowing:

1. A brand mark and the hero line: **"What made you Qrious today?"**
2. A large free-text input where the visitor types their question.
3. A row of sample question cards below, to spark ideas and lower the
   "blank box" barrier.

## Current state

Static front-end. Submitting a question runs a visual-only animation and echoes
the query back — no search, no backend, no accounts. This is deliberate: the
goal is to nail the feel of the first interaction before wiring anything up.

## Constraints

- Plain HTML/CSS/JS, no build step.
- Must feel premium on first paint, offline, on any modern browser.
- Dark, glowing, animated direction (chosen with the user).

## Decisions

- Stack: plain HTML/CSS/JS (fast to preview, zero deps).
- Submit: visual only for now.
- Mood: dark, glowing, animated.
- Design rationale and tokens documented in `DESIGN.md`.

## Next

- Real question answering / routing to a learning view.
- Persist recent questions; account entry point.
- Responsive/mobile polish pass and copy review.
