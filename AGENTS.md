# Qriously — Agent Guide

## What this is

Static marketing/landing homepage for **Qriously**, a learning platform. The
hero invites a visitor with "What made you Qrious today?" plus a free-text
input and sample question cards.

## Stack

Plain HTML, CSS, and vanilla JS. No build step, no npm, no framework.

## Files

- `index.html` — page structure and content.
- `styles.css` — all styling, design tokens, animation.
- `script.js` — interaction (input handling, sample cards, particle canvas).
- `DESIGN.md` — the design system: palette, type, motion, and rationale.

## Conventions

- Keep it dependency-free and offline-capable. No CDN fonts required for the
  page to look correct.
- Design tokens live as CSS custom properties in `:root` in `styles.css`.
  Change a token there, not scattered literals.
- Respect `prefers-reduced-motion` for every animation.
- Accessibility: real `<button>`/`<input>` elements, visible focus rings,
  keyboard-operable samples, sufficient contrast on the dark background.
- No comments in code unless they earn their place.

## Run

Open `index.html` directly, or serve the folder:

```bash
python3 -m http.server 8000
```

## Current state

Front-end only. Submit is visual: it animates and echoes the query. No backend.
