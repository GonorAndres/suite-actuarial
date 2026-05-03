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
      className={`overflow-x-auto rounded-xl border border-navy/10 ${className}`}
    >
      <table className="w-full text-left">
        <thead>
          <tr
            className={[
              highlightHeader ? "bg-navy" : "bg-navy/80",
              "first:[&>th]:rounded-tl-xl last:[&>th]:rounded-tr-xl",
            ].join(" ")}
          >
            {headers.map((header) => (
              <th
                key={header}
                scope="col"
                className="text-cream text-left text-sm font-medium px-4 py-3"
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
              className={[
                "border-b border-navy/5 hover:bg-amber/8 transition-colors duration-150",
                rowIdx % 2 === 1 ? "bg-navy/[0.02]" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {row.map((cell, cellIdx) => {
                const numeric = isNumericValue(cell);
                const currency = isCurrencyValue(cell);
                return (
                  <td
                    key={cellIdx}
                    className={[
                      "px-4 py-3 text-sm",
                      numeric ? "text-right tabular-nums" : "",
                      currency ? "font-semibold" : "",
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
