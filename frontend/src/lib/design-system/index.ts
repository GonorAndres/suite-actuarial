/**
 * Design System -- Public API
 *
 * Usage:
 *   import { cn, theme } from "@/lib/design-system";
 */

import clsx, { type ClassValue } from "clsx";

export { theme } from "./theme";
export type { Theme } from "./theme";

/**
 * Merge class names, filtering out falsy values.
 * Wraps clsx for conditional / composable Tailwind classes.
 *
 * @example
 *   cn("px-4 py-2", isActive && "bg-terracotta", className)
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
