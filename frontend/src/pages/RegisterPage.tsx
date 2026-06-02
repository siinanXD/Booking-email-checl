import { FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useAuthStore } from "@/stores/authStore";

type AccountType = "private" | "business";

export function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [accountType, setAccountType] = useState<AccountType>("private");
  const [companyName, setCompanyName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const register = useAuthStore((s) => s.register);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      const result = await register({
        email,
        password,
        password_confirm: passwordConfirm,
        first_name: firstName,
        last_name: lastName,
        phone,
        account_type: accountType,
        company_name: accountType === "business" ? companyName : undefined,
      });
      setSuccess(result.message);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } } })?.response?.data
          ?.error ?? "Registrierung fehlgeschlagen.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <Card className="w-full max-w-lg">
        <h1 className="text-xl font-semibold text-slate-900">Konto anlegen</h1>
        <p className="mt-1 text-sm text-slate-500">
          Nach der Registrierung prüfen wir dein Konto manuell.
        </p>

        {success ? (
          <div className="mt-6 space-y-4">
            <p className="rounded-lg bg-green-50 p-4 text-sm text-green-800">
              {success}
            </p>
            <Link to="/login">
              <Button className="w-full">Zur Anmeldung</Button>
            </Link>
          </div>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm text-slate-600">
                  Vorname
                </label>
                <Input
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">
                  Nachname
                </label>
                <Input
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm text-slate-600">
                E-Mail
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="username"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm text-slate-600">
                Telefon
              </label>
              <Input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+49..."
                required
              />
            </div>

            <div>
              <span className="mb-2 block text-sm text-slate-600">
                Nutzungsart
              </span>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="accountType"
                    checked={accountType === "private"}
                    onChange={() => setAccountType("private")}
                  />
                  Privat
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="accountType"
                    checked={accountType === "business"}
                    onChange={() => setAccountType("business")}
                  />
                  Gewerblich
                </label>
              </div>
            </div>

            {accountType === "business" && (
              <div>
                <label className="mb-1 block text-sm text-slate-600">
                  Firmenname
                </label>
                <Input
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                />
              </div>
            )}

            <div>
              <label className="mb-1 block text-sm text-slate-600">
                Passwort
              </label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm text-slate-600">
                Passwort bestätigen
              </label>
              <Input
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Wird gesendet…" : "Registrieren"}
            </Button>

            <p className="text-center text-sm text-slate-500">
              Bereits ein Konto?{" "}
              <Link to="/login" className="text-indigo-600 hover:underline">
                Anmelden
              </Link>
            </p>
          </form>
        )}
      </Card>
    </div>
  );
}
