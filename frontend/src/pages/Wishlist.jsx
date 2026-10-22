import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';

export default function Wishlist() {
  const [items, setItems] = useState([]);

  const load = () =>
    api
      .get('/wishlist/')
      .then((r) => setItems(r.data))
      .catch(() => toast.error('Wishlist unavailable'));

  useEffect(() => {
    load();
  }, []);

  const rm = async (id) => {
    await api.delete(`/wishlist/${id}`);
    load();
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Wishlist</h1>
      <div className="grid gap-4 md:grid-cols-3">
        {items.map((p) => (
          <div key={p.id} className="rounded-3xl border border-zinc-200 bg-white p-4 shadow-sm">
            <Link to={`/products/${p.id}`} className="text-sm font-semibold hover:text-orange-700">
              {p.name}
            </Link>
            <p className="mt-2 text-lg font-bold text-orange-600">${Number(p.price).toFixed(2)}</p>
            <button
              type="button"
              onClick={() => rm(p.id)}
              className="mt-3 w-full rounded-2xl border border-zinc-200 py-2 text-xs font-semibold hover:bg-red-50"
            >
              Remove
            </button>
          </div>
        ))}
        {items.length === 0 && <p className="text-sm text-zinc-500">Nothing saved yet.</p>}
      </div>
    </div>
  );
}
