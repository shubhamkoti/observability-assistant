import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';

export default function Seller() {
  const [stats, setStats] = useState(null);
  const [orders, setOrders] = useState([]);
  const [product, setProduct] = useState({
    name: '',
    description: '',
    price: '',
    sku: '',
    category_slug: 'electronics',
    initial_stock: '5',
    reorder_threshold: '5',
    compare_at_price: '',
  });
  const [inventoryForm, setInventoryForm] = useState({ product_id: '', quantity: '', price: '' });

  const load = () => {
    api.get('/seller/analytics/sales').then((r) => setStats(r.data)).catch(() => {});
    api
      .get('/seller/orders')
      .then((r) => setOrders(r.data))
      .catch(() => toast.error('Could not load seller orders'));
  };

  useEffect(() => {
    load();
  }, []);

  const submitProduct = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: product.name,
        description: product.description,
        price: Number(product.price),
        sku: product.sku || null,
        category_slug: product.category_slug || null,
        initial_stock: Number(product.initial_stock),
        reorder_threshold: Number(product.reorder_threshold),
        compare_at_price: product.compare_at_price ? Number(product.compare_at_price) : null,
      };
      await api.post('/products/seller', payload);
      toast.success('Submitted for moderation');
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Create failed');
    }
  };

  const patchInventory = async (e) => {
    e.preventDefault();
    try {
      const pid = Number(inventoryForm.product_id);
      const body = {};
      if (inventoryForm.quantity !== '') body.quantity = Number(inventoryForm.quantity);
      if (inventoryForm.price !== '') body.price = Number(inventoryForm.price);
      await api.patch(`/seller/products/${pid}`, body);
      toast.success('SKU updated');
    } catch {
      toast.error('Inventory update failed');
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Seller workspace</h1>
          <p className="text-sm text-zinc-500">Listings queue for admin moderation by default.</p>
        </div>
        {stats && (
          <div className="rounded-3xl border border-zinc-200 bg-white px-5 py-3 text-sm shadow-sm">
            <div>
              Revenue: <span className="font-semibold">${Number(stats.revenue).toFixed(2)}</span>
            </div>
            <div>
              Units: <span className="font-semibold">{stats.units_sold}</span>
            </div>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <form className="space-y-3 rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm" onSubmit={submitProduct}>
          <h2 className="font-semibold">New product</h2>
          <input
            className="w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="Name"
            value={product.name}
            required
            onChange={(e) => setProduct({ ...product, name: e.target.value })}
          />
          <textarea
            className="w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="Description"
            rows={3}
            value={product.description}
            onChange={(e) => setProduct({ ...product, description: e.target.value })}
          />
          <div className="grid gap-2 sm:grid-cols-2">
            <input
              className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
              placeholder="Price"
              type="number"
              step="0.01"
              required
              value={product.price}
              onChange={(e) => setProduct({ ...product, price: e.target.value })}
            />
            <input
              className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
              placeholder="Compare-at (optional)"
              type="number"
              step="0.01"
              value={product.compare_at_price}
              onChange={(e) => setProduct({ ...product, compare_at_price: e.target.value })}
            />
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <input
              className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
              placeholder="SKU"
              value={product.sku}
              onChange={(e) => setProduct({ ...product, sku: e.target.value })}
            />
            <input
              className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
              placeholder="Category slug (electronics)"
              value={product.category_slug}
              onChange={(e) => setProduct({ ...product, category_slug: e.target.value })}
            />
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <input
              className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
              placeholder="Initial stock"
              type="number"
              value={product.initial_stock}
              onChange={(e) => setProduct({ ...product, initial_stock: e.target.value })}
            />
            <input
              className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
              placeholder="Reorder threshold"
              type="number"
              value={product.reorder_threshold}
              onChange={(e) => setProduct({ ...product, reorder_threshold: e.target.value })}
            />
          </div>
          <button type="submit" className="w-full rounded-2xl bg-orange-500 py-2 text-sm font-semibold text-white">
            Submit listing
          </button>
        </form>

        <form className="space-y-3 rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm" onSubmit={patchInventory}>
          <h2 className="font-semibold">Inventory / price</h2>
          <input
            className="w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="Product ID"
            type="number"
            required
            value={inventoryForm.product_id}
            onChange={(e) => setInventoryForm({ ...inventoryForm, product_id: e.target.value })}
          />
          <input
            className="w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="New quantity (optional)"
            type="number"
            value={inventoryForm.quantity}
            onChange={(e) => setInventoryForm({ ...inventoryForm, quantity: e.target.value })}
          />
          <input
            className="w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="New price (optional)"
            type="number"
            step="0.01"
            value={inventoryForm.price}
            onChange={(e) => setInventoryForm({ ...inventoryForm, price: e.target.value })}
          />
          <button type="submit" className="w-full rounded-2xl bg-zinc-900 py-2 text-sm font-semibold text-white">
            Apply changes
          </button>
        </form>
      </div>

      <section className="rounded-3xl border border-zinc-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold">Orders touching your catalog</h2>
        <div className="mt-3 max-h-64 overflow-y-auto text-sm">
          <table className="min-w-full text-left">
            <thead className="text-xs uppercase text-zinc-400">
              <tr>
                <th className="px-2 py-2">#</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Total</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-t border-zinc-100">
                  <td className="px-2 py-2 font-semibold">{o.id}</td>
                  <td className="px-2 py-2">{o.status}</td>
                  <td className="px-2 py-2">${Number(o.total).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!orders.length && <p className="py-4 text-xs text-zinc-400">No intersecting orders yet.</p>}
        </div>
      </section>
    </div>
  );
}
