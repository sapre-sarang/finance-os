import type { ButtonHTMLAttributes, ReactNode } from "react";
import { ApiError } from "../lib/api";

export const inputClass =
  "w-full rounded border border-rule bg-sheet px-3 py-2 text-ink placeholder:text-muted";

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "quiet" | "danger" }) {
  const styles = {
    primary: "bg-ink text-sheet border-ink",
    quiet: "bg-sheet text-ink border-rule",
    danger: "bg-sheet text-danger border-rule",
  }[variant];
  return (
    <button
      type="button"
      {...props}
      className={`rounded border px-4 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50 ${styles} ${className}`}
    />
  );
}

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-semibold">{label}</span>
      {children}
      {hint ? <span className="mt-1 block text-sm text-muted">{hint}</span> : null}
    </label>
  );
}

export function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null;
  const problems =
    error instanceof ApiError ? error.problems : ["Something went wrong. Try again."];
  return (
    <div role="alert" className="rounded border-l-4 border-danger bg-sheet px-3 py-2 text-sm">
      {problems.length === 1 ? (
        problems[0]
      ) : (
        <ul className="list-disc pl-5">
          {problems.map((problem) => (
            <li key={problem}>{problem}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function Amount({ text, minor }: { text: string; minor: number }) {
  const tone = minor > 0 ? "text-credit" : minor < 0 ? "text-debit" : "text-muted";
  return <span className={`num whitespace-nowrap ${tone}`}>{text}</span>;
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded border border-dashed border-rule px-4 py-8 text-center">
      <p className="font-serif text-lg font-bold">{title}</p>
      {children ? <div className="mt-1 text-muted">{children}</div> : null}
    </div>
  );
}
