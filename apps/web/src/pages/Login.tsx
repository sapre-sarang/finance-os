import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { z } from "zod";
import { ErrorNote, Field, Button, inputClass } from "../components/ui";
import { ApiError, sendJson } from "../lib/api";
import { userSchema } from "../lib/schemas";

const loginSchema = z.object({
  username: z.string().trim().min(1, "Enter your username"),
  password: z.string().min(1, "Enter your password"),
});

export function Login() {
  const queryClient = useQueryClient();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const login = useMutation({
    mutationFn: (body: z.infer<typeof loginSchema>) =>
      sendJson("POST", "/auth/login", body, userSchema),
    onSuccess: (user) => queryClient.setQueryData(["me"], user),
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    const parsed = loginSchema.safeParse({ username, password });
    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Check your details");
      return;
    }
    setFormError(null);
    login.mutate(parsed.data);
  }

  return (
    <div className="mx-auto max-w-sm px-4 pt-24">
      <h1 className="text-4xl font-bold">FinanceOS</h1>
      <p className="mt-2 text-muted">Your accounts and statements, kept on your own machine.</p>
      <form onSubmit={submit} className="mt-8 space-y-4">
        <Field label="Username">
          <input
            className={inputClass}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
          />
        </Field>
        <Field label="Password">
          <input
            className={inputClass}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </Field>
        {formError ? <ErrorNote error={new ApiError(0, [formError])} /> : null}
        <ErrorNote error={login.error} />
        <Button type="submit" disabled={login.isPending}>
          {login.isPending ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </div>
  );
}
