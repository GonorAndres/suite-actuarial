/**
 * Renders one `<script type="application/ld+json">` block.
 *
 * Server Component on purpose: every route page in this app is `"use client"`,
 * so the JSON-LD is emitted from the sibling `layout.tsx` that already carries
 * the route's `Metadata`. That keeps the markup in the statically exported HTML
 * instead of behind hydration.
 *
 * A document may carry several of these blocks; consumers merge them, so a
 * route-level node can reference an `@id` declared by the root layout.
 */

/** A schema.org node. Shapes vary by @type, so the value side stays open. */
export type JsonLdNode = Record<string, unknown>;

export function StructuredData({ graph }: { graph: JsonLdNode[] }) {
  const payload = JSON.stringify({
    "@context": "https://schema.org",
    "@graph": graph,
  })
    // A literal "</script>" inside the JSON would close the tag early.
    .replace(/</g, "\\u003c");

  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: payload }} />;
}
