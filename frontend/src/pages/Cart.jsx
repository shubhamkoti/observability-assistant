import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';

export default function Cart() {
  const [cart, setCart] = useState(null);

  const load = () =>
    api
      .get('/cart/')
      .then((r) => setCart(r.data))
      .catch(() => toast.error('Failed to load cart'));

  useEffect(() => {
    load();
  }, []);

  const bump = async (productId, quantity) => {
    try {
      await api.post('/cart/', { product_id: productId, quantity });
      await load();
    } catch {
      toast.error('Update failed');
    }
  };

  if (!cart) {
    return <div className="py-24 text-center text-sm text-zinc-500">Loading cart…</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Cart</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() =>
              api
                .delete('/cart/')
                .then(() => load())
                .then(() => toast.success('Cart cleared'))
                .catch(() => toast.error('Clear failed'))
            }
            className="rounded-full border px-4 py-2 text-xs font-medium hover:bg-zinc-50"
          >
            Clear
          </button>
          <Link
            to="/checkout"
            className={`rounded-full bg-orange-500 px-4 py-2 text-xs font-semibold text-white shadow ${
              !cart.lines.length ? 'pointer-events-none opacity-40' : 'hover:bg-orange-600'
            }`}
          >
            Checkout
          </Link>
        </div>
      </div>

      {!cart.lines.length && <p className="text-sm text-zinc-500">Your cart is empty.</p>}

      <ul className="space-y-4">
        {cart.lines.map((line) => (
          <li
            key={line.product_id}
            className="flex flex-col justify-between gap-3 rounded-3xl border border-zinc-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center"
          >
            <div className="text-sm font-semibold">Product #{line.product_id}</div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="rounded-full bg-zinc-100 px-2 py-1 text-xs"
                onClick={() => bump(line.product_id, Math.max(0, line.quantity - 1))}
              >
                −
              </button>
              <span className="text-sm font-medium">{line.quantity}</span>
              <button
                type="button"
                className="rounded-full bg-zinc-100 px-2 py-1 text-xs"
                onClick={() => bump(line.product_id, line.quantity + 1)}
              >
                +
              </button>
            </div>
            <div className="text-sm">
              ${(Number(line.price_snapshot) * line.quantity).toFixed(2)}
            </div>
            <Link to={`/products/${line.product_id}`} className="text-xs text-orange-700 hover:underline">
              Details
            </Link>
          </li>
        ))}
      </ul>
      <div className="flex justify-end text-lg font-bold text-zinc-900">
        Subtotal: ${Number(cart.subtotal).toFixed(2)}
      </div>
    </div>
  );
}
