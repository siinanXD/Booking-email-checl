import { FormEvent, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { Input } from "@/shared/ui/Input";
import { useAuthStore } from "@/features/auth/authStore";
import { isAxiosError } from "axios";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    const { accessToken, user, logout } = useAuthStore.getState();
    if (accessToken && !user) {
      logout();
    }
  }, []);

  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        if (!err.response) {
          setError(
            "Server nicht erreichbar. Backend starten (Flask :5000 oder Docker :8000) und Seite neu laden."
          );
        } else if (err.response.data?.error) {
          setError(String(err.response.data.error));
        } else {
          setError("Anmeldung fehlgeschlagen. E-Mail oder Passwort prüfen.");
        }
      } else {
        setError("Anmeldung fehlgeschlagen. E-Mail oder Passwort prüfen.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <Card className="w-full max-w-md">
        <h1 className="text-xl font-semibold text-slate-900">AI Mail Platform</h1>
        <p className="mt-1 text-sm text-slate-500">Bitte anmelden</p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 block text-sm text-slate-600">E-Mail</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="username"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-600">Passwort</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Wird angemeldet…" : "Anmelden"}
          </Button>
          <p className="text-center text-sm text-slate-500">
            Noch kein Konto?{" "}
            <Link to="/register" className="text-indigo-600 hover:underline">
              Registrieren
            </Link>
          </p>
        </form>
      </Card>
    </div>
  );
}
