/**
 * Design System -- Single Source of Truth
 *
 * Edit this file to change colors, fonts, spacing, shadows, or transitions
 * across the entire app. CSS custom properties in tokens.css should stay
 * in sync with the values here.
 */

export const theme = {
  colors: {
    navy: "#1B2A4A",
    terracotta: "#C17654",
    sage: "#7A8B6F",
    cream: "#E8E0D7",
    offwhite: "#F5F0EA",
    amber: "#D4A574",
  },

  fonts: {
    heading: "Lora, Georgia, serif",
    body: "Inter, system-ui, sans-serif",
  },

  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
    "2xl": "3rem",
    "3xl": "4rem",
  },

  radii: {
    sm: "0.375rem",
    md: "0.5rem",
    lg: "0.75rem",
    xl: "1rem",
    full: "9999px",
  },

  shadows: {
    card: "0 1px 3px rgba(27, 42, 74, 0.08)",
    cardHover: "0 8px 30px rgba(27, 42, 74, 0.12)",
    input: "0 1px 2px rgba(27, 42, 74, 0.05)",
  },

  transitions: {
    fast: "150ms ease",
    normal: "300ms ease",
    slow: "500ms ease",
  },
} as const;

export type Theme = typeof theme;
