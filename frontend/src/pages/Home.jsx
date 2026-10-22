import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';

export default function Home() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState('');
  const [categories, setCategories] = useState([]);
  const [cat, setCat] = useState('');
  const [recs, setRecs] = useState(null);

  useEffect(() => {
    api
      .get('/categories/')
      .then((r) => setCategories(r.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const params = {};
    if (q) params.q = q;
    if (cat) params.category_id = Number(cat);
    api
      .get('/products/', { params })
      .then((r) => setItems(r.data))
      .catch(() => toast.error('Failed to load catalog'));
  }, [q, cat]);

  useEffect(() => {
    api
      .get('/recommendations/')
      .then((r) => setRecs(r.data))
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      <section className="rounded-3xl bg-gradient-to-br from-orange-600 via-amber-500 to-yellow-400 p-10 text-white shadow-xl">
        <p className="text-sm font-semibold uppercase tracking-wider text-white/80">Full-stack DBMS lab</p>
        <h1 className="mt-2 max-w-3xl text-4xl font-bold tracking-tight md:text-5xl">
          Search, wishlist, checkout, and dashboards — backed by PostgreSQL + MongoDB.
        </h1>
        <p className="mt-4 max-w-2xl text-sm md:text-base text-white/90">
          Row-level locking, triggers, views, JSON activity logs, JWT RBAC, simulated payments, and transactional
          rollback paths.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <span className="rounded-full bg-black/20 px-3 py-1 text-xs font-medium">ACID checkout</span>
          <span className="rounded-full bg-black/20 px-3 py-1 text-xs font-medium">Alembic migrations</span>
          <span className="rounded-full bg-black/20 px-3 py-1 text-xs font-medium">Audit + analytics</span>
        </div>
      </section>

      <div className="grid gap-10 md:grid-cols-[2fr,1fr]">
        <div className="space-y-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-xl font-semibold">Featured catalog</h2>
              <p className="text-sm text-zinc-500">JOIN-ready product grid with fast filters.</p>
            </div>
            <div className="flex flex-1 flex-col gap-2 md:max-w-xl md:flex-row">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search products..."
                className="w-full rounded-2xl border border-zinc-200 bg-white px-4 py-2 text-sm outline-none ring-orange-500/40 focus:ring-2"
              />
              <select
                value={cat}
                onChange={(e) => setCat(e.target.value)}
                className="rounded-2xl border border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-orange-500/40"
              >
                <option value="">All categories</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
            {items.length === 0 && (
              <div className="rounded-2xl border border-dashed border-zinc-200 bg-white p-6 text-sm text-zinc-500">
                No matches. Try adjusting filters.
              </div>
            )}
          </div>
        </div>
        <aside className="space-y-4 rounded-3xl border border-zinc-200 bg-white p-5 shadow-sm">
          <h3 className="font-semibold text-zinc-900">Top movers (view)</h3>
          <p className="text-xs text-zinc-500">v_top_selling_products + Mongo recommendation log.</p>
          <ul className="space-y-2 text-sm">
            {(recs?.items || []).map((r) => (
              <li key={r.product_id} className="flex items-center justify-between rounded-2xl bg-zinc-50 px-3 py-2">
                <span className="font-medium">{r.name}</span>
                <Link to={`/products/${r.product_id}`} className="text-xs text-orange-600 hover:underline">
                  View
                </Link>
              </li>
            ))}
            {(!recs || !recs.items?.length) && <li className="text-xs text-zinc-400">Place some orders to populate.</li>}
          </ul>
        </aside>
      </div>
    </div>
  );
}

function ProductCard({ product }) {
  return (
    <Link
      to={`/products/${product.id}`}
      className="group rounded-3xl border border-zinc-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-orange-200 hover:shadow-md"
    >
      <div className="mb-3 aspect-[4/3] w-full rounded-2xl bg-gradient-to-br from-zinc-100 to-zinc-200" />
      <h3 className="line-clamp-2 text-sm font-semibold text-zinc-900">{product.name}</h3>
      <p className="mt-2 text-lg font-bold text-orange-600">${Number(product.price).toFixed(2)}</p>
      <p className="mt-1 text-xs text-zinc-400">Tap for details, reviews, and stock</p>
    </Link>
  );
}
