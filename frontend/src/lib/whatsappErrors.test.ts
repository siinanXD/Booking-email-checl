import { describe, expect, it } from "vitest";
import { parseWhatsAppErrorHint } from "@/lib/whatsappErrors";

describe("parseWhatsAppErrorHint", () => {
  it("recognizes the allowed-list error (131030)", () => {
    const hint = parseWhatsAppErrorHint(
      "Fehler: Meta API (400, code 131030): Recipient phone number not in allowed list"
    );
    expect(hint?.code).toBe(131030);
    expect(hint?.title).toContain("Testmodus");
    expect(hint?.actionUrl).toBeTruthy();
  });

  it("recognizes other known codes", () => {
    expect(parseWhatsAppErrorHint("Meta API (401, code 190): token expired")?.code).toBe(
      190
    );
    expect(parseWhatsAppErrorHint("code 133010 ...")?.code).toBe(133010);
  });

  it("returns null for unknown codes", () => {
    expect(parseWhatsAppErrorHint("Meta API (400, code 999999): something")).toBeNull();
  });

  it("returns null when no code is present", () => {
    expect(parseWhatsAppErrorHint("WhatsApp-Test fehlgeschlagen.")).toBeNull();
    expect(parseWhatsAppErrorHint(null)).toBeNull();
    expect(parseWhatsAppErrorHint(undefined)).toBeNull();
  });
});
