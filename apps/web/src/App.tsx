import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ApiError } from "./lib/api";
import { useMe } from "./lib/queries";
import { Accounts } from "./pages/Accounts";
import { Import } from "./pages/Import";
import { Login } from "./pages/Login";
import { Overview } from "./pages/Overview";
import { Transactions } from "./pages/Transactions";

export function App() {
  const me = useMe();

  if (me.isPending) return <p className="p-8 text-muted">Loading…</p>;
  if (me.isError) {
    if (me.error instanceof ApiError && me.error.status === 401) return <Login />;
    return (
      <p role="alert" className="p-8">
        Cannot reach the FinanceOS server. Start the API and refresh this page.
      </p>
    );
  }

  return (
    <Routes>
      <Route element={<Layout username={me.data.username} />}>
        <Route index element={<Overview />} />
        <Route path="transactions" element={<Transactions />} />
        <Route path="accounts" element={<Accounts />} />
        <Route path="import" element={<Import />} />
        <Route path="*" element={<p>That page does not exist.</p>} />
      </Route>
    </Routes>
  );
}
