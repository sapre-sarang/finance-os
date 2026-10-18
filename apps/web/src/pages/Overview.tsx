import { Link } from "react-router-dom";
import { Amount, Empty } from "../components/ui";
import { ACCOUNT_KIND_LABELS } from "../lib/schemas";
import { useAccounts, useCurrencies, useSummary } from "../lib/queries";

export function Overview() {
  const summary = useSummary();
  const accounts = useAccounts();
  const money = useCurrencies();

  if (summary.isPending || accounts.isPending) return <p className="text-muted">Loading…</p>;
  if (summary.isError || accounts.isError) {
    return <p role="alert">Could not load your overview. Refresh to try again.</p>;
  }
  if (accounts.data.length === 0) {
    return (
      <Empty title="No accounts yet">
        <Link className="text-credit underline" to="/accounts">
          Add your first account
        </Link>{" "}
        to start tracking.
      </Empty>
    );
  }

  return (
    <div className="space-y-10">
      <section aria-labelledby="nw">
        <h1 id="nw" className="text-lg font-bold text-muted">
          Net worth
        </h1>
        {summary.data.net_worth.map((total) => (
          <p key={total.currency} className="mt-1 font-serif text-5xl font-bold">
            <Amount
              minor={total.net_worth_minor}
              text={money.format(total.net_worth_minor, total.currency)}
            />
          </p>
        ))}
        <p className="mt-2 max-w-prose text-sm text-muted">
          Opening balances plus every transaction you have entered or imported. Credit cards and
          loans count against it when their balance is negative.
        </p>
      </section>

      <section aria-labelledby="acc">
        <h2 id="acc" className="mb-2 text-2xl font-bold">
          Accounts
        </h2>
        <ul className="border-t-2 border-ink">
          {accounts.data.map((account) => (
            <li
              key={account.id}
              className="flex items-baseline justify-between gap-4 border-b border-rule py-3"
            >
              <div>
                <Link
                  to={`/transactions?account=${account.id}`}
                  className="font-semibold underline-offset-4 hover:underline"
                >
                  {account.name}
                </Link>
                <p className="text-sm text-muted">
                  {ACCOUNT_KIND_LABELS[account.kind]}
                  {account.identifier_hint ? ` ${account.identifier_hint}` : ""}
                </p>
              </div>
              <Amount
                minor={account.balance_minor}
                text={money.format(account.balance_minor, account.currency)}
              />
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
