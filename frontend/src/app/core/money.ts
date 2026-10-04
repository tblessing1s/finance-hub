const usd = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const usdWhole = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

/** Format a decimal-string amount from the API. Whole-dollar amounts drop the cents. */
export function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '';
  const n = typeof value === 'number' ? value : Number(value);
  if (Number.isNaN(n)) return String(value);
  return Number.isInteger(n) ? usdWhole.format(n) : usd.format(n);
}

/** Form input (number or string) to the API's two-place decimal string, or null when blank. */
export function toApiMoney(value: number | string | null | undefined): string | null {
  if (value === null || value === undefined || value === '') return null;
  const n = typeof value === 'number' ? value : Number(value);
  if (Number.isNaN(n)) return null;
  return n.toFixed(2);
}

/** API decimal string to a number for an <input type="number">. */
export function fromApiMoney(value: string | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(value);
  return Number.isNaN(n) ? null : n;
}
