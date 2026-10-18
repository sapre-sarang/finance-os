import { useQuery } from "@tanstack/react-query";
import { get } from "./api";
import { formatMinor } from "./money";
import {
  accountListSchema,
  currencyListSchema,
  summarySchema,
  transactionPageSchema,
  userSchema,
} from "./schemas";

export const PAGE_SIZE = 25;

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => get("/auth/me", userSchema),
    retry: false,
    staleTime: 60_000,
  });
}

export function useAccounts() {
  return useQuery({ queryKey: ["accounts"], queryFn: () => get("/accounts", accountListSchema) });
}

export function useSummary() {
  return useQuery({ queryKey: ["summary"], queryFn: () => get("/summary", summarySchema) });
}

export function useTransactions(accountId: string, page: number) {
  const params = new URLSearchParams({
    limit: String(PAGE_SIZE),
    offset: String(page * PAGE_SIZE),
  });
  if (accountId) params.set("account_id", accountId);
  return useQuery({
    queryKey: ["transactions", accountId, page],
    queryFn: () => get(`/transactions?${params}`, transactionPageSchema),
  });
}

export function useCurrencies() {
  const query = useQuery({
    queryKey: ["currencies"],
    queryFn: () => get("/currencies", currencyListSchema),
    staleTime: Infinity,
  });
  const digits = (code: string): number =>
    query.data?.find((c) => c.code === code)?.minor_unit_digits ?? 2;
  return {
    codes: query.data?.map((c) => c.code) ?? [],
    digits,
    format: (minor: number, code: string) => formatMinor(minor, code, digits(code)),
  };
}
