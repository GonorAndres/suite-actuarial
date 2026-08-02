/**
 * Formatting and download utilities.
 */

/**
 * Format a number as Mexican currency: "$1,234.56 MXN"
 */
export function formatCurrency(value: number, decimals = 2): string {
  const formatted = value.toLocaleString("es-MX", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return `$${formatted} MXN`;
}

/**
 * Format a fraction as a percentage: 0.1234 -> "12.34%".
 *
 * Use only when the API sends a fraction of one. When the API already sends
 * the value in percent points (40.0 for 40%), use `formatPercentValue`:
 * multiplying twice is the classic 100x display error.
 */
export function formatPercent(value: number, decimals = 2): string {
  const pct = value * 100;
  return `${pct.toFixed(decimals)}%`;
}

/**
 * Format a value already expressed in percent points: 40.0 -> "40.00%".
 */
export function formatPercentValue(value: number, decimals = 2): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format a rate quoted per mille (por millar): 0.8 -> "0.80 ‰".
 *
 * Property, liability, and health base rates in this package are quoted per
 * thousand of the insured value, not per hundred.
 */
export function formatPerMille(value: number, decimals = 2): string {
  return `${value.toFixed(decimals)} ‰`;
}

/**
 * Format a number with thousand separators.
 */
export function formatNumber(value: number, decimals = 2): string {
  return value.toLocaleString("es-MX", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Trigger a CSV file download in the browser.
 */
export function downloadCSV(
  data: Record<string, unknown>[],
  filename: string,
): void {
  if (data.length === 0) return;

  const headers = Object.keys(data[0]);
  const csvRows = [
    headers.join(","),
    ...data.map((row) =>
      headers
        .map((h) => {
          const val = row[h];
          const str = val === null || val === undefined ? "" : String(val);
          // Escape double quotes and wrap in quotes if necessary
          if (str.includes(",") || str.includes('"') || str.includes("\n")) {
            return `"${str.replace(/"/g, '""')}"`;
          }
          return str;
        })
        .join(","),
    ),
  ];

  const blob = new Blob([csvRows.join("\n")], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.endsWith(".csv") ? filename : `${filename}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Trigger a JSON file download in the browser.
 */
export function downloadJSON(data: unknown, filename: string): void {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: "application/json;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename.endsWith(".json") ? filename : `${filename}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
