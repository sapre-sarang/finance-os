import { z } from "zod";

export const ACCOUNT_KINDS = ["checking", "savings", "credit_card", "loan", "cash"] as const;
export type AccountKind = (typeof ACCOUNT_KINDS)[number];

export const ACCOUNT_KIND_LABELS: Record<AccountKind, string> = {
  checking: "Checking",
  savings: "Savings",
  credit_card: "Credit card",
  loan: "Loan",
  cash: "Cash",
};

export const userSchema = z.object({ username: z.string() });

export const accountSchema = z.object({
  id: z.string(),
  name: z.string(),
  kind: z.enum(ACCOUNT_KINDS),
  currency: z.string(),
  opening_balance_minor: z.number().int(),
  balance_minor: z.number().int(),
  identifier_hint: z.string().nullable(),
});
export type Account = z.infer<typeof accountSchema>;
export const accountListSchema = z.array(accountSchema);

export const transactionSchema = z.object({
  id: z.string(),
  account_id: z.string(),
  occurred_on: z.string(),
  amount_minor: z.number().int(),
  currency: z.string(),
  description: z.string(),
  imported: z.boolean(),
});
export type Transaction = z.infer<typeof transactionSchema>;

export const transactionPageSchema = z.object({
  items: z.array(transactionSchema),
  total: z.number().int(),
});

export const summarySchema = z.object({
  net_worth: z.array(z.object({ currency: z.string(), net_worth_minor: z.number().int() })),
});

export const currencyListSchema = z.array(
  z.object({ code: z.string(), minor_unit_digits: z.number().int() }),
);

export const inspectSchema = z.object({
  headers: z.array(z.string()),
  sample_rows: z.array(z.array(z.string())),
});

export const previewSchema = z.object({
  rows: z.array(
    z.object({
      index: z.number().int(),
      occurred_on: z.string(),
      amount_minor: z.number().int(),
      currency: z.string(),
      description: z.string(),
      already_imported: z.boolean(),
    }),
  ),
  new_count: z.number().int(),
  already_imported_count: z.number().int(),
});
export type Preview = z.infer<typeof previewSchema>;

export const commitSchema = z.object({
  added: z.number().int(),
  already_imported: z.number().int(),
  skipped_by_you: z.number().int(),
});
