# Qriously — Agent Guide

## What this is

**Qriously**, a learning platform, in two parts:

1. **Landing designs** — nine standalone homepage directions built around
   "What made you Qrious today?"
2. **The immersive app** (`app/`) — the product: branching, non-linear
   exploration where any span can be dived into without losing context.
   Spec-first; see `app/INTERACTION-SPEC.md`.

## Structure

Each design direction is a **standalone, self-contained page in its own folder**.
No shared CSS/JS between designs — a design can be lifted out on its own.

```text
qriously/
├── index.html          # chooser linking to every landing design
├── DESIGN.md           # landing design system + rationale for each direction
├── nocturne/           # dark, glowing, animated
├── daylight/           # light, airy, editorial
├── playtime/           # playful, colorful
├── blueprint/          # technical drawing
├── riso/               # two-spot zine print
├── atelier/            # luxury editorial
├── liquidglass/        # premium glassmorphism
├── questlog/           # RPG HUD with XP
├── clay/               # claymorphism
└── app/                # immersive learning app (prototype)
    ├── INTERACTION-SPEC.md  # the interaction spec (read first)
    ├── index.html
    ├── styles.css           # Lumen reading-first theme
    ├── content.js           # mock node graph + generator
    └── script.js            # branching engine
```

The landing folders are independent, self-contained pages. The `app/` folder is
the actual product surface; read `app/INTERACTION-SPEC.md` before working on it.
Run it by opening `app/index.html`, or append `?demo=1` to load a pre-seeded
branching session (useful for screenshots and manual testing).

Every design folder has the same three files:

- `index.html` — page structure and content.
- `styles.css` — all styling for that direction.
- `script.js` — interaction (input, sample cards, submit feedback).

## Stack

Plain HTML, CSS, and vanilla JS. No build step, no npm, no framework. Fonts are
loaded from Google Fonts but every page degrades to system fonts.

## Conventions

- Keep each design dependency-free and offline-capable.
- Design tokens live as CSS custom properties in `:root` of that design's
  `styles.css`.
- Respect `prefers-reduced-motion` for every animation.
- Accessibility: real `<button>`/`<input>` elements, visible focus rings,
  keyboard-operable samples, sufficient contrast.
- No comments in code unless they earn their place.

## Run

Open the root `index.html` for the chooser, or a design's `index.html`
directly. To serve the whole project:

```bash
python3 -m http.server 8000
```

## Current state

Front-end only. Submit is visual: it animates and echoes the query. No backend.

`questlog/` additionally maintains a local XP/level state in the HUD, but it is
in-memory only and resets on reload.
