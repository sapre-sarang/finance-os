import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Amount, Button, Empty, ErrorNote, Field, inputClass } from "../components/ui";
import { sendForm } from "../lib/api";
import { useAccounts, useCurrencies } from "../lib/queries";
import { commitSchema, inspectSchema, previewSchema } from "../lib/schemas";

const DATE_FORMATS = [
  { value: "%d/%m/%Y", label: "Day/Month/Year (04/03/2025)" },
  { value: "%m/%d/%Y", label: "Month/Day/Year (03/04/2025)" },
  { value: "%Y-%m-%d", label: "Year-Month-Day (2025-03-04)" },
  { value: "%d-%m-%Y", label: "Day-Month-Year (04-03-2025)" },
  { value: "%d/%m/%y", label: "Day/Month/Short year (04/03/25)" },
  { value: "%d %b %Y", label: "Day Mon Year (04 Mar 2025)" },
];

type AmountMode = "signed" | "split";

interface Mapping {
  dateColumn: string;
  descriptionColumn: string;
  dateFormat: string;
  amountMode: AmountMode;
  amountColumn: string;
  debitColumn: string;
  creditColumn: string;
  referenceColumn: string;
}

function guess(headers: string[], ...needles: string[]): string {
  return (
    headers.find((h) => needles.some((n) => h.toLowerCase().includes(n))) ?? ""
  );
}

function guessMapping(headers: string[]): Mapping {
  const debit = guess(headers, "debit", "withdraw", "paid out");
  const credit = guess(headers, "credit", "deposit", "paid in");
  const amount = guess(headers, "amount");
  return {
    dateColumn: guess(headers, "date"),
    descriptionColumn: guess(headers, "narration", "description", "details", "particulars"),
    dateFormat: "%d/%m/%Y",
    amountMode: !amount && debit && credit ? "split" : "signed",
    amountColumn: amount,
    debitColumn: debit,
    creditColumn: credit,
    referenceColumn: guess(headers, "ref", "cheque", "utr", "transaction id"),
  };
}

function buildForm(accountId: string, file: File, m: Mapping, skip: number[] = []): FormData {
  const form = new FormData();
  form.set("account_id", accountId);
  form.set("file", file);
  form.set("date_column", m.dateColumn);
  form.set("description_column", m.descriptionColumn);
  form.set("date_format", m.dateFormat);
  form.set("reference_column", m.referenceColumn);
  if (m.amountMode === "signed") form.set("amount_column", m.amountColumn);
  else {
    form.set("debit_column", m.debitColumn);
    form.set("credit_column", m.creditColumn);
  }
  if (skip.length > 0) form.set("skip_rows", skip.join(","));
  return form;
}

export function Import() {
  const accounts = useAccounts();
  const money = useCurrencies();
  const queryClient = useQueryClient();

  const [accountId, setAccountId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [mapping, setMapping] = useState<Mapping | null>(null);
  const [skipped, setSkipped] = useState<Set<number>>(new Set());

  const inspect = useMutation({
    mutationFn: (selected: File) => {
      const form = new FormData();
      form.set("file", selected);
      return sendForm("/imports/inspect", form, inspectSchema);
    },
    onSuccess: (result) => setMapping(guessMapping(result.headers)),
  });
  const preview = useMutation({
    mutationFn: () => {
      if (!file || !mapping) throw new Error("missing file");
      return sendForm("/imports/preview", buildForm(target, file, mapping), previewSchema);
    },
    onSuccess: () => setSkipped(new Set()),
  });
  const commit = useMutation({
    mutationFn: () => {
      if (!file || !mapping) throw new Error("missing file");
      return sendForm(
        "/imports/commit",
        buildForm(target, file, mapping, [...skipped]),
        commitSchema,
      );
    },
    onSuccess: () => void queryClient.invalidateQueries(),
  });

  const target = accountId || accounts.data?.[0]?.id || "";
  const account = accounts.data?.find((a) => a.id === target);

  function reset() {
    setFile(null);
    setMapping(null);
    inspect.reset();
    preview.reset();
    commit.reset();
  }

  function choose(selected: File | null) {
    reset();
    setFile(selected);
    if (selected) inspect.mutate(selected);
  }

  const set = <K extends keyof Mapping>(key: K, value: Mapping[K]) => {
    preview.reset();
    setMapping((current) => (current ? { ...current, [key]: value } : current));
  };

  if (accounts.data?.length === 0) {
    return (
      <Empty title="Add an account first">
        <Link className="text-credit underline" to="/accounts">
          Go to accounts
        </Link>{" "}
        so the statement has somewhere to go.
      </Empty>
    );
  }

  if (commit.data) {
    const done = commit.data;
    return (
      <div className="max-w-xl space-y-4">
        <h1 className="text-3xl font-bold">Import finished</h1>
        <p>
          Added <strong className="num">{done.added}</strong> transaction
          {done.added === 1 ? "" : "s"} to {account?.name}.
          {done.already_imported > 0
            ? ` ${done.already_imported} already existed and were left alone.`
            : ""}
          {done.skipped_by_you > 0 ? ` You skipped ${done.skipped_by_you}.` : ""}
        </p>
        <div className="flex gap-2">
          <Link
            to={`/transactions?account=${target}`}
            className="rounded border border-ink bg-ink px-4 py-2 text-sm font-semibold text-sheet"
          >
            View transactions
          </Link>
          <Button variant="quiet" onClick={reset}>
            Import another file
          </Button>
        </div>
      </div>
    );
  }

  const headers = inspect.data?.headers ?? [];
  const columnSelect = (value: string, onChange: (v: string) => void, optional = false) => (
    <select className={inputClass} value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">{optional ? "None" : "Choose a column"}</option>
      {headers.map((h) => (
        <option key={h} value={h}>
          {h}
        </option>
      ))}
    </select>
  );
  const ready =
    mapping !== null &&
    mapping.dateColumn !== "" &&
    mapping.descriptionColumn !== "" &&
    (mapping.amountMode === "signed"
      ? mapping.amountColumn !== ""
      : mapping.debitColumn !== "" && mapping.creditColumn !== "");

  return (
    <div className="max-w-4xl space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Import a statement</h1>
        <p className="mt-1 max-w-prose text-muted">
          Upload a CSV export from your bank. Nothing is saved until you review the rows and
          confirm. Importing the same file twice never adds duplicates.
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2" aria-label="Choose file">
        <Field label="Import into">
          <select
            className={inputClass}
            value={target}
            onChange={(e) => {
              setAccountId(e.target.value);
              preview.reset();
            }}
          >
            {accounts.data?.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} ({a.currency})
              </option>
            ))}
          </select>
        </Field>
        <Field label="Statement file (.csv)" hint="Up to 5 MB.">
          <input
            className={inputClass}
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => choose(e.target.files?.[0] ?? null)}
          />
        </Field>
      </section>

      <ErrorNote error={inspect.error} />

      {mapping && inspect.data ? (
        <section className="space-y-4" aria-labelledby="map">
          <h2 id="map" className="text-xl font-bold">
            Match the columns
          </h2>
          <div className="overflow-x-auto rounded border border-rule bg-sheet">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-rule">
                  {headers.map((h) => (
                    <th key={h} className="px-3 py-2 font-semibold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {inspect.data.sample_rows.map((row, i) => (
                  <tr key={i} className="border-b border-rule last:border-0">
                    {headers.map((h, c) => (
                      <td key={h} className="whitespace-nowrap px-3 py-1.5 text-muted">
                        {row[c]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Date column">{columnSelect(mapping.dateColumn, (v) => set("dateColumn", v))}</Field>
            <Field label="Date format">
              <select
                className={inputClass}
                value={mapping.dateFormat}
                onChange={(e) => set("dateFormat", e.target.value)}
              >
                {DATE_FORMATS.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Description column">
              {columnSelect(mapping.descriptionColumn, (v) => set("descriptionColumn", v))}
            </Field>
            <Field label="Bank reference column" hint="Optional. A unique reference makes duplicate detection exact.">
              {columnSelect(mapping.referenceColumn, (v) => set("referenceColumn", v), true)}
            </Field>
            <Field label="Amounts are in">
              <select
                className={inputClass}
                value={mapping.amountMode}
                onChange={(e) => set("amountMode", e.target.value as AmountMode)}
              >
                <option value="signed">One column (negative = money out)</option>
                <option value="split">Separate debit and credit columns</option>
              </select>
            </Field>
            {mapping.amountMode === "signed" ? (
              <Field label="Amount column">
                {columnSelect(mapping.amountColumn, (v) => set("amountColumn", v))}
              </Field>
            ) : (
              <>
                <Field label="Debit column (money out)">
                  {columnSelect(mapping.debitColumn, (v) => set("debitColumn", v))}
                </Field>
                <Field label="Credit column (money in)">
                  {columnSelect(mapping.creditColumn, (v) => set("creditColumn", v))}
                </Field>
              </>
            )}
          </div>
          <Button disabled={!ready || preview.isPending} onClick={() => preview.mutate()}>
            {preview.isPending ? "Checking file…" : "Review rows"}
          </Button>
        </section>
      ) : null}

      <ErrorNote error={preview.error} />

      {preview.data && account ? (
        <section className="space-y-4" aria-labelledby="review">
          <h2 id="review" className="text-xl font-bold">
            Review before importing
          </h2>
          <p>
            <strong className="num">{preview.data.new_count}</strong> new,{" "}
            <strong className="num">{preview.data.already_imported_count}</strong> already in{" "}
            {account.name}. Untick any new row you do not want.
          </p>
          <div className="max-h-[28rem] overflow-auto">
            <table className="w-full border-t-2 border-ink text-left">
              <thead>
                <tr className="border-b border-rule text-sm text-muted">
                  <th className="py-2 pr-3">
                    <span className="sr-only">Include</span>
                  </th>
                  <th className="py-2 pr-4 font-semibold">Date</th>
                  <th className="py-2 pr-4 font-semibold">Description</th>
                  <th className="py-2 text-right font-semibold">Amount</th>
                </tr>
              </thead>
              <tbody>
                {preview.data.rows.map((row) => (
                  <tr
                    key={row.index}
                    className={`border-b border-rule ${row.already_imported ? "text-muted" : ""}`}
                  >
                    <td className="py-2 pr-3">
                      {row.already_imported ? null : (
                        <input
                          type="checkbox"
                          aria-label={`Include ${row.description}`}
                          checked={!skipped.has(row.index)}
                          onChange={(e) =>
                            setSkipped((current) => {
                              const next = new Set(current);
                              if (e.target.checked) next.delete(row.index);
                              else next.add(row.index);
                              return next;
                            })
                          }
                        />
                      )}
                    </td>
                    <td className="num whitespace-nowrap py-2 pr-4">{row.occurred_on}</td>
                    <td className="py-2 pr-4">
                      {row.description}
                      {row.already_imported ? (
                        <span className="ml-2 rounded bg-debit-soft px-1.5 py-0.5 text-xs text-ink">
                          already in account
                        </span>
                      ) : null}
                    </td>
                    <td className="py-2 text-right">
                      <Amount
                        minor={row.amount_minor}
                        text={money.format(row.amount_minor, row.currency)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ErrorNote error={commit.error} />
          <Button
            disabled={commit.isPending || preview.data.new_count - skipped.size === 0}
            onClick={() => commit.mutate()}
          >
            {commit.isPending
              ? "Importing…"
              : `Import ${preview.data.new_count - skipped.size} row${preview.data.new_count - skipped.size === 1 ? "" : "s"}`}
          </Button>
        </section>
      ) : null}
    </div>
  );
}
