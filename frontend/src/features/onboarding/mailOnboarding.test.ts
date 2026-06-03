import { describe, expect, it } from "vitest";
import { needsMailOnboarding } from "./mailOnboarding";

describe("needsMailOnboarding", () => {
  it("returns false for platform_admin", () => {
    expect(
      needsMailOnboarding({
        role: "platform_admin",
        account_status: "active",
        mail_onboarding_completed: false,
      })
    ).toBe(false);
  });

  it("returns true for owner without completed onboarding", () => {
    expect(
      needsMailOnboarding({
        role: "owner",
        account_status: "active",
        mail_onboarding_completed: false,
      })
    ).toBe(true);
  });

  it("returns false for member", () => {
    expect(
      needsMailOnboarding({
        role: "member",
        account_status: "active",
        mail_onboarding_completed: false,
      })
    ).toBe(false);
  });
});
