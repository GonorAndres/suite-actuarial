interface TableProps {
  headers: string[];
  rows: (string | number)[][];
  className?: string;
  highlightHeader?: boolean;
}

/** Detect if a cell value looks like a currency string (starts with $) */
function isCurrencyValue(val: string | number): boolean {
  if (typeof val === "number") return false;
  return /^\$/.test(val.trim());
}

/** Detect if a cell value looks numeric */
function isNumericValue(val: string | number): boolean {
  if (typeof val === "number") return true;
  return /^[\$\-\d,.\s%]+$/.test(val.trim()) && val.trim().length > 0;
}

export default function Table({
  headers,
  rows,
  className = "",
  highlightHeader = true,
}: TableProps) {
  return (
    <div
      className={`overflow-x-auto rounded-sm border border-navy/15 bg-white ${className}`}
    >
      <table className="w-full text-left">
        <thead>
          <tr
            className={
              highlightHeader
                ? "border-b-2 border-navy"
                : "border-b border-navy/30"
            }
          >
            {headers.map((header) => (
              <th
                key={header}
                scope="col"
                className="text-navy text-left text-xs font-bold uppercase tracking-widest px-5 py-3.5"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className="border-b border-navy/10 last:border-b-0 transition-colors hover:bg-cream/50"
            >
              {row.map((cell, cellIdx) => {
                const numeric = isNumericValue(cell);
                const currency = isCurrencyValue(cell);
                return (
                  <td
                    key={cellIdx}
                    className={[
                      "px-5 py-3 text-sm",
                      numeric ? "text-right tabular-nums" : "",
                      currency ? "font-semibold" : "",
                      cellIdx === 0 ? "font-medium text-navy/80" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    {cell}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
