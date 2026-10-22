import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';

export default function Admin() {
  const [dash, setDash] = useState(null);
  const [top, setTop] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [pending, setPending] = useState([]);
  const [audit, setAudit] = useState([]);

  const load = async () => {
    try {
      const [d, t, m, p, a] = await Promise.all([
        api.get('/admin/analytics/dashboard'),
        api.get('/admin/analytics/top-products'),
        api.get('/admin/analytics/monthly'),
        api.get('/admin/products/pending'),
        api.get('/admin/audit/sql?limit=40'),
      ]);
      setDash(d.data);
      setTop(t.data.data || []);
      setMonthly(m.data.data || []);
      setPending(p.data);
      setAudit(a.data);
    } catch {
      toast.error('Admin data failed (forbidden?)');
    }
  };

  useEffect(() => {
    load();
  }, []);

  const moderate = async (id, status) => {
    try {
      await api.patch(`/admin/products/${id}/moderation`, { status });
      toast.success('Moderation updated');
      load();
    } catch {
      toast.error('Moderation failed');
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Admin console</h1>
        <p className="text-sm text-zinc-500">PostgreSQL views + SQL audit + moderation queue.</p>
      </div>

      {dash && (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ['Users', dash.total_users],
            ['Products', dash.total_products],
            ['Orders', dash.total_orders],
            ['Revenue (paid)', `$${Number(dash.revenue_completed).toFixed(2)}`],
          ].map(([k, v]) => (
            <div key={k} className="rounded-3xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-zinc-400">{k}</p>
              <p className="mt-2 text-2xl font-bold">{v}</p>
            </div>
          ))}
        </section>
      )}

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl border border-zinc-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold">v_top_selling_products</h2>
          <ul className="mt-3 max-h-64 space-y-2 overflow-y-auto text-sm">
            {top.map((row) => (
              <li key={row.product_id} className="flex justify-between rounded-2xl bg-zinc-50 px-3 py-2">
                <span>{row.name}</span>
                <span className="text-xs text-zinc-500">{row.units_sold} sold</span>
              </li>
            ))}
            {!top.length && <li className="text-xs text-zinc-400">No sales yet.</li>}
          </ul>
        </div>
        <div className="rounded-3xl border border-zinc-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold">v_monthly_sales</h2>
          <ul className="mt-3 max-h-64 space-y-2 overflow-y-auto text-sm">
            {monthly.map((row, idx) => (
              <li key={idx} className="flex justify-between rounded-2xl bg-zinc-50 px-3 py-2">
                <span className="text-xs">{String(row.month)}</span>
                <span>${Number(row.total_sales).toFixed(2)}</span>
              </li>
            ))}
            {!monthly.length && <li className="text-xs text-zinc-400">Empty.</li>}
          </ul>
        </div>
      </section>

      <section className="rounded-3xl border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold">Moderation queue</h2>
        <div className="mt-4 space-y-3">
          {pending.map((pr) => (
            <div key={pr.id} className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-zinc-100 px-3 py-2 text-sm">
              <div>
                <span className="font-semibold">{pr.name}</span>
                <span className="ml-2 text-xs text-zinc-500">seller #{pr.seller_user_id}</span>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => moderate(pr.id, 'approved')}
                  className="rounded-full bg-emerald-600 px-3 py-1 text-xs font-semibold text-white"
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => moderate(pr.id, 'rejected')}
                  className="rounded-full bg-red-600 px-3 py-1 text-xs font-semibold text-white"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
          {!pending.length && <p className="text-sm text-zinc-400">No pending listings.</p>}
        </div>
      </section>

      <section className="rounded-3xl border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold">sql_audit_log (trigger feed)</h2>
        <div className="mt-3 max-h-64 space-y-2 overflow-y-auto font-mono text-xs">
          {audit.map((row) => (
            <div key={row.id} className="rounded-xl bg-zinc-50 px-2 py-1">
              <span className="text-orange-700">{row.action}</span> · {row.table_name} #{row.entity_id}
              <div className="text-zinc-500">{row.payload_preview}</div>
            </div>
          ))}
          {!audit.length && <p className="text-zinc-400">No audit rows yet. Delete a product to fire trigger.</p>}
        </div>
      </section>
    </div>
  );
}
