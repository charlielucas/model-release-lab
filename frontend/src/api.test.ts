import { afterEach, describe, expect, it, vi } from "vitest";

import { createRun, getScenarios } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("API client", () => {
  it("loads the allowlisted scenarios", async () => {
    const payload = [{ scenario_id: "clean-release", name: "Clean release" }];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ));

    await expect(getScenarios()).resolves.toEqual(payload);
  });

  it("preserves a bounded API error message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Unknown scenario" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    ));

    await expect(createRun("missing")).rejects.toThrow("Unknown scenario");
  });
});
