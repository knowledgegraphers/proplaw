# Frontend Rules

These rules apply to everything under `propra/frontend/`. The universal conventions (product tone, German output, mobile optimisation is never skipped) are in the root `CLAUDE.md`.

- Every page and component must be **mobile-first** — design for 375px minimum width before considering desktop.
- Use **Tailwind CSS utility classes only**. Do not create custom CSS files unless there is no Tailwind equivalent.
- **Primary colour:** deep navy `#1A3355`
- **Accent colour:** warm amber `#C9952A`
- **Typography:**
  - Headlines: DM Serif Display (serif)
  - Body: DM Sans (sans-serif)
- **No dark mode** in MVP.
- Every form field must have a visible **German-language label and placeholder**.
- All buttons must have a **loading state**.
- No page should require **horizontal scrolling on mobile**.
