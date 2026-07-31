import { describe, expect, it } from "vitest";

import { percent, shortDigest } from "./format";

describe("format helpers", () => {
  it("formats percentages without hiding a material decimal", () => {
    expect(percent(0.825)).toBe("82.5%");
  });

  it("keeps both ends of an evidence digest", () => {
    expect(shortDigest("1234567890abcdefghijklmnop")).toBe("1234567890...klmnop");
  });
});
