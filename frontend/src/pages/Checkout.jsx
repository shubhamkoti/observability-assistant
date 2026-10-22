import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';

export default function Checkout() {
  const navigate = useNavigate();
  const [addresses, setAddresses] = useState([]);
  const [addressId, setAddressId] = useState('');
  const [coupon, setCoupon] = useState('');
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [cart, setCart] = useState(null);

  useEffect(() => {
    api.get('/addresses/').then((r) => {
      setAddresses(r.data);
      const def = r.data.find((a) => a.is_default)?.id ?? r.data[0]?.id;
      if (def) {
        setAddressId(String(def));
      }
    });
    api.get('/cart/').then((r) => setCart(r.data));
  }, []);

  const place = async (e) => {
    e.preventDefault();
    if (!addressId) {
      toast.error('Add an address first');
      return;
    }
    try {
      const res = await api.post('/orders/checkout', {
        address_id: Number(addressId),
        coupon_code: coupon.trim() || null,
        simulate_failure: simulateFailure,
      });
      toast.success(`Order #${res.data.order.id} created · payment ${res.data.payment.status}`);
      navigate('/orders');
    } catch (err) {
      const d = err.response?.data?.detail;
      toast.error(Array.isArray(d) ? JSON.stringify(d) : d || 'Checkout failed');
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Checkout</h1>
        <p className="text-sm text-zinc-500">Create the order first, then trigger a fake payment from order history.</p>
      </div>
      {cart && (
        <div className="rounded-3xl border border-zinc-200 bg-white p-4 text-sm">
          Lines:{' '}
          <span className="font-semibold">{cart.lines.length}</span> · Subtotal $
          <span className="font-semibold">{Number(cart.subtotal).toFixed(2)}</span>
        </div>
      )}
      <form className="space-y-4 rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm" onSubmit={place}>
        <label className="block text-sm font-semibold">
          Ship to
          <select
            required
            className="mt-2 w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            value={addressId}
            onChange={(e) => setAddressId(e.target.value)}
          >
            <option value="">Select saved address…</option>
            {addresses.map((a) => (
              <option key={a.id} value={a.id}>
                {a.label} — {a.line1}, {a.city}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-semibold">
          Coupon (try SAVE10)
          <input
            className="mt-2 w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            value={coupon}
            onChange={(e) => setCoupon(e.target.value)}
            placeholder="Optional"
          />
        </label>
        <label className="flex items-center gap-2 text-sm text-zinc-600">
          <input type="checkbox" checked={simulateFailure} onChange={(e) => setSimulateFailure(e.target.checked)} />
          Simulate payment failure (forces DB rollback)
        </label>
        <button
          type="submit"
          className="w-full rounded-2xl bg-orange-500 py-2.5 text-sm font-semibold text-white hover:bg-orange-600"
        >
          Place order
        </button>
      </form>
    </div>
  );
}
