import { useMutation, useQueryClient } from "@tanstack/react-query";
import { NavLink, Outlet } from "react-router-dom";
import { postNoContent } from "../lib/api";
import { Button } from "./ui";

const LINKS = [
  { to: "/", label: "Overview", end: true },
  { to: "/transactions", label: "Transactions", end: false },
  { to: "/accounts", label: "Accounts", end: false },
  { to: "/import", label: "Import", end: false },
];

export function Layout({ username }: { username: string }) {
  const queryClient = useQueryClient();
  const signOut = useMutation({
    mutationFn: () => postNoContent("/auth/logout"),
    onSuccess: () => queryClient.clear(),
  });

  return (
    <div className="mx-auto max-w-5xl px-4 pb-16">
      <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-b-2 border-ink py-4">
        <p className="font-serif text-2xl font-bold">FinanceOS</p>
        <nav aria-label="Main" className="order-3 flex w-full gap-5 sm:order-none sm:w-auto">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `border-b-2 py-1 ${isActive ? "border-credit font-semibold" : "border-transparent text-muted"}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-muted">{username}</span>
          <Button variant="quiet" onClick={() => signOut.mutate()}>
            Sign out
          </Button>
        </div>
      </header>
      <main className="pt-8">
        <Outlet />
      </main>
    </div>
  );
}
