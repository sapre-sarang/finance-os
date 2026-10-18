import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Amount, Button, Empty, ErrorNote, Field, inputClass } from "../components/ui";
import { ApiError, remove, sendJson } from "../lib/api";
import { parseAmountToMinor } from "../lib/money";
import { PAGE_SIZE, useAccounts, useCurrencies, useTransactions } from "../lib/queries";
import { transactionSchema } from "../lib/schemas";

const today = () => new Date().toLocaleDateString("en-CA");

export function Transactions() {
  const [params, setParams] = useSearchParams();
  const accountId = params.get("account") ?? "";
  const [page, setPage] = useState(0);
  const accounts = useAccounts();
  const transactions = useTransactions(accountId, page);
  const money = useCurrencies();
  const queryClient = useQueryClient();

  const [formAccount, setFormAccount] = useState("");
  const [date, setDate] = useState(today);
  const [direction, setDirection] = useState<"out" | "in">("out");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [formError, setFormError] = useState<ApiError | null>(null);

  const refresh = () => queryClient.invalidateQueries();
  const create = useMutation({
    mutationFn: (body: unknown) => sendJson("POST", "/transactions", body, transactionSchema),
    onSuccess: () => {
      setAmount("");
      setDescription("");
      void refresh();
    },
  });
  const del = useMutation({
    mutationFn: (id: string) => remove(`/transactions/${id}`),
    onSuccess: () => void refresh(),
  });

  const accountById = new Map(accounts.data?.map((a) => [a.id, a]));
  const targetId = formAccount || accountId || accounts.data?.[0]?.id || "";
  const target = accountById.get(targetId);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!target) return setFormError(new ApiError(0, ["Choose an account"]));
    const minor = parseAmountToMinor(amount, money.digits(target.currency));
    if (minor === null || minor <= 0) {
      return setFormError(
        new ApiError(0, [
          `Enter a positive amount with up to ${money.digits(target.currency)} decimal places`,
        ]),
      );
    }
    if (description.trim() === "") return setFormError(new ApiError(0, ["Add a description"]));
    setFormError(null);
    create.mutate({
      account_id: target.id,
      occurred_on: date,
      amount_minor: direction === "out" ? -minor : minor,
      description: description.trim(),
    });
  }

  if (accounts.data?.length === 0) {
    return (
      <Empty title="Add an account first">
        <Link className="text-credit underline" to="/accounts">
          Go to accounts
        </Link>
      </Empty>
    );
  }

  const total = transactions.data?.total ?? 0;
  const lastPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="text-3xl font-bold">Transactions</h1>
        <label className="text-sm">
          <span className="mr-2 font-semibold">Account</span>
          <select
            className="rounded border border-rule bg-sheet px-3 py-2"
            value={accountId}
            onChange={(e) => {
              setPage(0);
              setParams(e.target.value ? { account: e.target.value } : {});
            }}
          >
            <option value="">All accounts</option>
            {accounts.data?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <form
        onSubmit={submit}
        className="grid gap-3 rounded border border-rule bg-sheet p-4 sm:grid-cols-6"
      >
        <div className="sm:col-span-2">
          <Field label="Account">
            <select
              className={inputClass}
              value={targetId}
              onChange={(e) => setFormAccount(e.target.value)}
            >
              {accounts.data?.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <Field label="Date">
          <input
            className={inputClass}
            type="date"
            value={date}
            min="1990-01-01"
            onChange={(e) => setDate(e.target.value)}
          />
        </Field>
        <Field label="Direction">
          <select
            className={inputClass}
            value={direction}
            onChange={(e) => setDirection(e.target.value as "out" | "in")}
          >
            <option value="out">Money out</option>
            <option value="in">Money in</option>
          </select>
        </Field>
        <Field label={`Amount${target ? ` (${target.currency})` : ""}`}>
          <input
            className={`${inputClass} num`}
            inputMode="decimal"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </Field>
        <div className="sm:col-span-4">
          <Field label="Description">
            <input
              className={inputClass}
              value={description}
              maxLength={500}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Field>
        </div>
        <div className="flex items-end sm:col-span-2">
          <Button type="submit" disabled={create.isPending}>
            Add transaction
          </Button>
        </div>
        <div className="sm:col-span-6 empty:hidden">
          <ErrorNote error={formError ?? create.error} />
        </div>
      </form>

      <ErrorNote error={del.error} />
      {transactions.isPending ? <p className="text-muted">Loading…</p> : null}
      {transactions.data && transactions.data.items.length === 0 ? (
        <Empty title="No transactions yet">
          Add one above, or{" "}
          <Link className="text-credit underline" to="/import">
            import a statement
          </Link>
          .
        </Empty>
      ) : null}
      {transactions.data && transactions.data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[32rem] border-t-2 border-ink text-left">
              <thead>
                <tr className="border-b border-rule text-sm text-muted">
                  <th className="py-2 pr-4 font-semibold">Date</th>
                  <th className="py-2 pr-4 font-semibold">Description</th>
                  {accountId ? null : <th className="py-2 pr-4 font-semibold">Account</th>}
                  <th className="py-2 pr-4 text-right font-semibold">Amount</th>
                  <th className="py-2">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {transactions.data.items.map((t) => (
                  <tr key={t.id} className="border-b border-rule">
                    <td className="num whitespace-nowrap py-2 pr-4">{t.occurred_on}</td>
                    <td className="py-2 pr-4">
                      {t.description}
                      {t.imported ? (
                        <span className="ml-2 rounded bg-credit-soft px-1.5 py-0.5 text-xs">
                          imported
                        </span>
                      ) : null}
                    </td>
                    {accountId ? null : (
                      <td className="py-2 pr-4 text-sm text-muted">
                        {accountById.get(t.account_id)?.name}
                      </td>
                    )}
                    <td className="py-2 pr-4 text-right">
                      <Amount minor={t.amount_minor} text={money.format(t.amount_minor, t.currency)} />
                    </td>
                    <td className="py-2 text-right">
                      <Button
                        variant="danger"
                        aria-label={`Delete ${t.description}`}
                        onClick={() => {
                          if (window.confirm("Delete this transaction?")) del.mutate(t.id);
                        }}
                      >
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted">
              {total} transaction{total === 1 ? "" : "s"}
            </span>
            <div className="flex items-center gap-2">
              <Button variant="quiet" disabled={page === 0} onClick={() => setPage(page - 1)}>
                Newer
              </Button>
              <span className="num">
                Page {page + 1} of {lastPage + 1}
              </span>
              <Button variant="quiet" disabled={page >= lastPage} onClick={() => setPage(page + 1)}>
                Older
              </Button>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
