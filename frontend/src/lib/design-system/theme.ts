/**
 * Design System -- Single Source of Truth
 *
 * Editorial palette: classic-insurance ink and paper with an oxblood accent.
 * Token keys keep their historical names (navy/terracotta/sage/cream/offwhite/
 * amber) so existing utility classes keep working; the values define the roles
 * ink / accent / green / surface / paper / gold.
 *
 * Edit this file to change colors, fonts, spacing, shadows, or transitions
 * across the entire app. CSS custom properties in tokens.css should stay
 * in sync with the values here.
 */

export const theme = {
  colors: {
    /** Ink -- primary text and headers */
    navy: "#1A2740",
    /** Oxblood accent -- links, active states, primary emphasis */
    terracotta: "#8A3B34",
    /** Deep institutional green -- success states */
    sage: "#38664A",
    /** Secondary paper surface */
    cream: "#F2EEE4",
    /** Primary paper surface */
    offwhite: "#FBF9F5",
    /** Aged gold -- rules, borders, restrained highlights */
    amber: "#9C7A2F",
  },

  /**
   * Categorical chart series, in fixed assignment order.
   * Validated (CVD + normal-vision + lightness/chroma) against the paper
   * surface #FBF9F5; gold sits below 3:1 contrast, so charts using it must
   * keep visible labels, legends, or tooltips (they all do).
   */
  chart: {
    series1: "#2A5FA8", // blue
    series2: "#BC4B3C", // brick
    series3: "#C99117", // gold
    series4: "#1F6B3A", // green
    ink: "#1A2740",
    paper: "#FBF9F5",
  },

  fonts: {
    heading: "Playfair Display, Georgia, serif",
    body: "Source Sans 3, system-ui, sans-serif",
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
    sm: "0.25rem",
    md: "0.375rem",
    lg: "0.5rem",
    xl: "0.75rem",
    full: "9999px",
  },

  shadows: {
    card: "0 1px 2px rgba(26, 39, 64, 0.06)",
    cardHover: "0 4px 16px rgba(26, 39, 64, 0.10)",
    input: "0 1px 2px rgba(26, 39, 64, 0.04)",
  },

  transitions: {
    fast: "150ms ease",
    normal: "300ms ease",
    slow: "500ms ease",
  },
} as const;

export type Theme = typeof theme;
