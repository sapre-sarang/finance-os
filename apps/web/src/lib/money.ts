// Amounts are integers in the currency's smallest unit. Nothing here converts
// through floating point: text is split on the decimal point and joined as digits.

const AMOUNT_PATTERN = /^[+-]?\d+(\.\d+)?$/;
export const MAX_MINOR = 10 ** 15;

export function parseAmountToMinor(text: string, minorUnitDigits: number): number | null {
  const cleaned = text.trim().replace(/[, ]/g, "");
  if (!AMOUNT_PATTERN.test(cleaned)) return null;

  const negative = cleaned.startsWith("-");
  const unsigned = cleaned.replace(/^[+-]/, "");
  const [whole = "", fraction = ""] = unsigned.split(".");
  if (fraction.length > minorUnitDigits) return null;

  const minor = Number(whole + fraction.padEnd(minorUnitDigits, "0"));
  if (!Number.isSafeInteger(minor) || minor >= MAX_MINOR) return null;
  return negative ? -minor : minor;
}

export function minorToDecimalString(minor: number, minorUnitDigits: number): string {
  const digits = BigInt(Math.abs(minor)).toString().padStart(minorUnitDigits + 1, "0");
  const whole = digits.slice(0, digits.length - minorUnitDigits);
  const fraction = minorUnitDigits > 0 ? `.${digits.slice(-minorUnitDigits)}` : "";
  return `${minor < 0 ? "-" : ""}${whole}${fraction}`;
}

const LOCALE_BY_CURRENCY: Record<string, string> = { INR: "en-IN" };
const SYMBOL_BY_CURRENCY: Record<string, string> = {
  INR: "₹",
  USD: "$",
  EUR: "€",
  GBP: "£",
  JPY: "¥",
};

export function formatMinor(minor: number, currency: string, minorUnitDigits: number): string {
  const negative = minor < 0;
  const digits = BigInt(Math.abs(minor)).toString().padStart(minorUnitDigits + 1, "0");
  const whole = digits.slice(0, digits.length - minorUnitDigits);
  const fraction = minorUnitDigits > 0 ? digits.slice(-minorUnitDigits) : "";

  const grouped = new Intl.NumberFormat(LOCALE_BY_CURRENCY[currency] ?? "en-US").format(
    BigInt(whole),
  );
  const symbol = SYMBOL_BY_CURRENCY[currency] ?? `${currency} `;
  const body = fraction ? `${grouped}.${fraction}` : grouped;
  return `${negative ? "−" : ""}${symbol}${body}`;
}
