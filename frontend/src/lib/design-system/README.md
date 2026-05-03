# Design System -- Suite Actuarial

Single source of truth for colors, typography, spacing, and component patterns.

## Quick Start

```ts
import { cn, theme } from "@/lib/design-system";
```

Edit `theme.ts` to change any token; update `tokens.css` to keep CSS custom
properties in sync.

---

## Color Palette

| Token        | Hex       | Usage                                |
|------------- |---------- |------------------------------------- |
| navy         | `#1B2A4A` | Text, headings, dark backgrounds     |
| terracotta   | `#C17654` | Primary actions, CTA buttons         |
| sage         | `#7A8B6F` | Secondary actions, success states    |
| cream        | `#E8E0D7` | Page background                      |
| offwhite     | `#F5F0EA` | Card backgrounds, elevated surfaces  |
| amber        | `#D4A574` | Accents, highlights, outline buttons |

## Typography

- **Headings**: Lora (serif) -- h1 through h4
- **Body**: Inter (sans-serif) -- paragraphs, labels, inputs

Tailwind classes: `font-heading`, `font-body`.

## Spacing Scale

| Token | Value    | Tailwind         |
|------ |--------- |----------------- |
| xs    | 0.25rem  | `p-1`, `gap-1`   |
| sm    | 0.5rem   | `p-2`, `gap-2`   |
| md    | 1rem     | `p-4`, `gap-4`   |
| lg    | 1.5rem   | `p-6`, `gap-6`   |
| xl    | 2rem     | `p-8`, `gap-8`   |
| 2xl   | 3rem     | `p-12`, `gap-12` |
| 3xl   | 4rem     | `p-16`, `gap-16` |

## Component Inventory

| Component      | File                          | Purpose                     |
|--------------- |------------------------------ |---------------------------- |
| Button         | `components/ui/Button.tsx`    | primary / secondary / outline variants |
| Card           | `components/ui/Card.tsx`      | Content container with optional hover  |
| Input          | `components/ui/Input.tsx`     | Text input with label       |
| Select         | `components/ui/Select.tsx`    | Dropdown selector           |
| Table          | `components/ui/Table.tsx`     | Data table                  |
| Badge          | `components/ui/Badge.tsx`     | Status indicators           |
| Tabs           | `components/ui/Tabs.tsx`      | Tab navigation              |
| LoadingSpinner | `components/ui/LoadingSpinner.tsx` | Loading state          |

All components are barrel-exported from `components/ui/index.ts`.

## Using `cn()`

The `cn` helper (wraps `clsx`) merges class names with falsy-value filtering:

```tsx
import { cn } from "@/lib/design-system";

<div className={cn(
  "bg-offwhite rounded-xl p-6",
  hoverable && "hover:shadow-lg",
  className,
)} />
```

## How to Modify the Theme

1. Open `src/lib/design-system/theme.ts` -- edit token values.
2. Mirror changes in `src/lib/design-system/tokens.css` (CSS custom properties).
3. If you add a new color, also register it in the `@theme inline` block inside
   `globals.css` so Tailwind generates utility classes for it.
4. Run `npx next build` to verify nothing breaks.

## How to Add a New Component

1. Create `src/components/ui/YourComponent.tsx`.
2. Import `cn` from `@/lib/design-system` for class composition.
3. Use Tailwind classes that reference design tokens (`bg-navy`, `text-cream`, etc.).
4. Export from `src/components/ui/index.ts`.

## File Map

```
src/lib/design-system/
  theme.ts      -- JS/TS token object (single source of truth)
  tokens.css    -- CSS custom properties (consumed by globals.css)
  index.ts      -- barrel exports + cn() utility
  README.md     -- this file
```
