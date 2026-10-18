import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Amount, Button, Empty, ErrorNote, Field, inputClass } from "../components/ui";
import { ApiError, remove, sendJson } from "../lib/api";
import { MAX_MINOR, minorToDecimalString, parseAmountToMinor } from "../lib/money";
import { useAccounts, useCurrencies } from "../lib/queries";
import {
  ACCOUNT_KINDS,
  ACCOUNT_KIND_LABELS,
  accountSchema,
  type Account,
  type AccountKind,
} from "../lib/schemas";

interface FormState {
  name: string;
  kind: AccountKind;
  currency: string;
  opening: string;
  identifier: string;
}

const BLANK: FormState = { name: "", kind: "checking", currency: "INR", opening: "0", identifier: "" };

export function Accounts() {
  const accounts = useAccounts();
  const money = useCurrencies();
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Account | null>(null);
  const [form, setForm] = useState<FormState>(BLANK);
  const [formError, setFormError] = useState<ApiError | null>(null);

  const refresh = () => queryClient.invalidateQueries();
  const save = useMutation({
    mutationFn: (body: unknown) => sendJson("POST", "/accounts", body, accountSchema),
    onSuccess: () => {
      reset();
      void refresh();
    },
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: unknown }) =>
      sendJson("PUT", `/accounts/${id}`, body, accountSchema),
    onSuccess: () => {
      reset();
      void refresh();
    },
  });
  const del = useMutation({
    mutationFn: (id: string) => remove(`/accounts/${id}`),
    onSuccess: () => void refresh(),
  });

  function reset() {
    setEditing(null);
    setForm(BLANK);
    setFormError(null);
  }

  function startEdit(account: Account) {
    setEditing(account);
    setFormError(null);
    setForm({
      name: account.name,
      kind: account.kind,
      currency: account.currency,
      opening: minorToDecimalString(
        account.opening_balance_minor,
        money.digits(account.currency),
      ),
      identifier: "",
    });
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const openingMinor = parseAmountToMinor(form.opening, money.digits(form.currency));
    if (form.name.trim() === "") return setFormError(new ApiError(0, ["Give the account a name"]));
    if (openingMinor === null || Math.abs(openingMinor) >= MAX_MINOR) {
      return setFormError(
        new ApiError(0, [
          `Enter the opening balance as a number with up to ${money.digits(form.currency)} decimal places`,
        ]),
      );
    }
    setFormError(null);
    const body = {
      name: form.name.trim(),
      kind: form.kind,
      currency: form.currency,
      opening_balance_minor: openingMinor,
      identifier: form.identifier.trim() || null,
    };
    if (editing) update.mutate({ id: editing.id, body });
    else save.mutate(body);
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((current) => ({ ...current, [key]: value }));
  const busy = save.isPending || update.isPending;

  return (
    <div className="grid gap-10 md:grid-cols-[1fr_20rem]">
      <section aria-labelledby="list">
        <h1 id="list" className="mb-2 text-3xl font-bold">
          Accounts
        </h1>
        <ErrorNote error={del.error} />
        {accounts.isPending ? <p className="text-muted">Loading…</p> : null}
        {accounts.data?.length === 0 ? (
          <Empty title="No accounts yet">Use the form to add one.</Empty>
        ) : (
          <ul className="border-t-2 border-ink">
            {accounts.data?.map((account) => (
              <li key={account.id} className="border-b border-rule py-3">
                <div className="flex items-baseline justify-between gap-4">
                  <div>
                    <p className="font-semibold">{account.name}</p>
                    <p className="text-sm text-muted">
                      {ACCOUNT_KIND_LABELS[account.kind]} · {account.currency}
                      {account.identifier_hint ? ` · ${account.identifier_hint}` : ""}
                    </p>
                  </div>
                  <Amount
                    minor={account.balance_minor}
                    text={money.format(account.balance_minor, account.currency)}
                  />
                </div>
                <div className="mt-2 flex gap-2">
                  <Button variant="quiet" onClick={() => startEdit(account)}>
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => {
                      if (
                        window.confirm(
                          `Delete ${account.name} and all of its transactions? This cannot be undone.`,
                        )
                      )
                        del.mutate(account.id);
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <form onSubmit={submit} className="space-y-4 self-start rounded border border-rule bg-sheet p-4">
        <h2 className="text-xl font-bold">{editing ? "Edit account" : "Add an account"}</h2>
        <Field label="Name">
          <input className={inputClass} value={form.name} onChange={(e) => set("name", e.target.value)} />
        </Field>
        <Field label="Type">
          <select
            className={inputClass}
            value={form.kind}
            onChange={(e) => set("kind", e.target.value as AccountKind)}
          >
            {ACCOUNT_KINDS.map((kind) => (
              <option key={kind} value={kind}>
                {ACCOUNT_KIND_LABELS[kind]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Currency" hint={editing ? "Fixed once an account has transactions" : undefined}>
          <select
            className={inputClass}
            value={form.currency}
            onChange={(e) => set("currency", e.target.value)}
          >
            {money.codes.map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </Field>
        <Field
          label="Opening balance"
          hint="What the account held before your first transaction. Use a negative number for money owed."
        >
          <input
            className={`${inputClass} num`}
            inputMode="decimal"
            value={form.opening}
            onChange={(e) => set("opening", e.target.value)}
          />
        </Field>
        <Field
          label="Account number (optional)"
          hint={
            editing?.identifier_hint
              ? "Leave blank to keep the saved number. It is stored encrypted."
              : "Stored encrypted; only the last 4 characters are ever shown."
          }
        >
          <input
            className={inputClass}
            value={form.identifier}
            maxLength={34}
            autoComplete="off"
            onChange={(e) => set("identifier", e.target.value)}
          />
        </Field>
        <ErrorNote error={formError ?? save.error ?? update.error} />
        <div className="flex gap-2">
          <Button type="submit" disabled={busy}>
            {editing ? "Save changes" : "Add account"}
          </Button>
          {editing ? (
            <Button variant="quiet" onClick={reset}>
              Cancel
            </Button>
          ) : null}
        </div>
      </form>
    </div>
  );
}
