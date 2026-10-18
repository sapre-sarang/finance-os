import { describe, expect, it } from "vitest";
import { formatMinor, minorToDecimalString, parseAmountToMinor } from "./money";

describe("parseAmountToMinor", () => {
  it("converts decimal text to integer minor units", () => {
    expect(parseAmountToMinor("1234.56", 2)).toBe(123456);
    expect(parseAmountToMinor("1,00,000.50", 2)).toBe(10000050);
    expect(parseAmountToMinor("500", 2)).toBe(50000);
    expect(parseAmountToMinor("500", 0)).toBe(500);
  });

  it("is exact where float math drifts", () => {
    expect(parseAmountToMinor("0.1", 2)).toBe(10);
    expect(parseAmountToMinor("1.15", 2)).toBe(115);
    expect(parseAmountToMinor("19.99", 2)).toBe(1999);
  });

  it("keeps the sign", () => {
    expect(parseAmountToMinor("-10.5", 2)).toBe(-1050);
    expect(parseAmountToMinor("+10.5", 2)).toBe(1050);
  });

  it("rejects anything that is not a plain amount", () => {
    for (const bad of ["", "abc", "1.2.3", "12.345", "1e3", "$5", "--5", "5.", ".5"]) {
      expect(parseAmountToMinor(bad, 2), bad).toBeNull();
    }
    expect(parseAmountToMinor("5.5", 0)).toBeNull();
  });

  it("rejects amounts the API would refuse", () => {
    expect(parseAmountToMinor("10000000000000.00", 2)).toBeNull();
  });
});

describe("minorToDecimalString", () => {
  it("round-trips with parseAmountToMinor", () => {
    for (const minor of [0, 5, -5, 123456, -10000050, 99]) {
      const text = minorToDecimalString(minor, 2);
      expect(parseAmountToMinor(text, 2), text).toBe(minor);
    }
    expect(minorToDecimalString(-1050, 2)).toBe("-10.50");
    expect(minorToDecimalString(500, 0)).toBe("500");
  });
});

describe("formatMinor", () => {
  it("formats with grouping and fixed decimals", () => {
    expect(formatMinor(123456, "USD", 2)).toBe("$1,234.56");
    expect(formatMinor(10000050, "INR", 2)).toBe("₹1,00,000.50");
    expect(formatMinor(500, "JPY", 0)).toBe("¥500");
  });

  it("pads small values and marks negatives", () => {
    expect(formatMinor(5, "INR", 2)).toBe("₹0.05");
    expect(formatMinor(-5, "INR", 2)).toBe("−₹0.05");
    expect(formatMinor(0, "INR", 2)).toBe("₹0.00");
  });
});
