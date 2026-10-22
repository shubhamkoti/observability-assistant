import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';

export default function Orders() {
  const [rows, setRows] = useState([]);

  const loadOrders = () => {
    api
      .get('/orders/mine')
      .then((r) => setRows(r.data))
      .catch(() => toast.error('Could not load orders'));
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const simulatePayment = async (orderId) => {
    try {
      const res = await api.post(`/orders/${orderId}/simulate-payment`);
      toast.success(`Payment ${res.data.status} for order #${orderId}`);
      loadOrders();
    } catch (err) {
      const detail = err.response?.data?.detail;
      toast.error(detail || 'Could not simulate payment');
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Order history</h1>
      <div className="overflow-hidden rounded-3xl border border-zinc-200 bg-white shadow-sm">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Order</th>
              <th className="px-4 py-3">Payment</th>
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">When</th>
              <th className="px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((o) => (
              <tr key={o.id} className="border-t border-zinc-100">
                <td className="px-4 py-3 font-semibold">#{o.id}</td>
                <td className="px-4 py-3">{o.status}</td>
                <td className="px-4 py-3">{o.payment_status ?? 'Missing'}</td>
                <td className="px-4 py-3">${Number(o.total).toFixed(2)}</td>
                <td className="px-4 py-3 text-xs text-zinc-500">{new Date(o.created_at).toLocaleString()}</td>
                <td className="px-4 py-3">
                  {o.payment_status === 'Pending' ? (
                    <button
                      type="button"
                      onClick={() => simulatePayment(o.id)}
                      className="rounded-full bg-orange-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-orange-600"
                    >
                      Simulate Payment
                    </button>
                  ) : (
                    <span className="text-xs text-zinc-400">{o.simulated_ref || 'Success'}</span>
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-sm text-zinc-500">
                  No orders yet.{' '}
                  <Link className="text-orange-700 hover:underline" to="/checkout">
                    Checkout
                  </Link>
                  .
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
