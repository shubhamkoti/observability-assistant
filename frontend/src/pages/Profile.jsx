import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';

const emptyAddr = {
  label: '',
  line1: '',
  city: '',
  state: '',
  postal_code: '',
  country: 'IN',
  is_default: true,
};

export default function Profile() {
  const { user, refresh } = useAuth();
  const [addresses, setAddresses] = useState([]);
  const [form, setForm] = useState(emptyAddr);
  const [notifications, setNotifications] = useState([]);

  const loadAddresses = () =>
    api
      .get('/addresses/')
      .then((r) => setAddresses(r.data))
      .catch(() => toast.error('Addresses failed'));

  const loadNotifs = () =>
    api
      .get('/notifications/')
      .then((r) => setNotifications(r.data))
      .catch(() => {});

  useEffect(() => {
    loadAddresses();
    loadNotifs();
  }, []);

  const saveAddress = async (e) => {
    e.preventDefault();
    try {
      await api.post('/addresses/', form);
      toast.success('Address saved');
      setForm(emptyAddr);
      loadAddresses();
    } catch {
      toast.error('Could not save address');
    }
  };

  const rmAddress = async (id) => {
    try {
      await api.delete(`/addresses/${id}`);
      loadAddresses();
    } catch {
      toast.error('Delete failed');
    }
  };

  const markRead = async () => {
    await api.post('/notifications/mark-all-read');
    loadNotifs();
    refresh();
  };

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <div className="rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-bold">Profile</h1>
        {user && (
          <div className="mt-4 space-y-1 text-sm">
            <p>
              <span className="font-semibold">{user.full_name}</span>
            </p>
            <p className="text-zinc-500">{user.email}</p>
            <p className="text-xs text-zinc-400">Roles: {(user.roles || []).map((r) => r.name).join(', ')}</p>
          </div>
        )}
      </div>

      <div className="rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Notifications</h2>
        <button
          type="button"
          onClick={markRead}
          className="mt-2 rounded-full border px-3 py-1 text-xs font-medium hover:bg-zinc-50"
        >
          Mark all read
        </button>
        <ul className="mt-4 max-h-52 space-y-2 overflow-y-auto text-sm">
          {notifications.map((n) => (
            <li key={n.id} className={`rounded-2xl px-3 py-2 ${n.is_read ? 'bg-zinc-50' : 'bg-orange-50'}`}>
              <div className="font-medium">{n.title}</div>
              {n.body && <div className="text-xs text-zinc-600">{n.body}</div>}
            </li>
          ))}
          {notifications.length === 0 && <li className="text-xs text-zinc-400">No notifications.</li>}
        </ul>
      </div>

      <div className="rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm lg:col-span-2">
        <h2 className="text-lg font-semibold">Saved addresses</h2>
        <ul className="mt-4 grid gap-3 md:grid-cols-2">
          {addresses.map((a) => (
            <li key={a.id} className="rounded-2xl border border-zinc-100 bg-zinc-50 p-3 text-sm">
              <div className="font-semibold">{a.label}</div>
              <div className="text-zinc-600">
                {a.line1}, {a.city}, {a.state} {a.postal_code}
              </div>
              {a.is_default && <span className="text-xs text-orange-700">Default</span>}
              <button
                type="button"
                onClick={() => rmAddress(a.id)}
                className="mt-2 w-full rounded-xl border border-red-200 py-1 text-xs text-red-700 hover:bg-red-50"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>

        <form className="mt-6 grid gap-2 border-t border-zinc-100 pt-6 md:grid-cols-2" onSubmit={saveAddress}>
          <p className="md:col-span-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">Add address</p>
          <input
            className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="Label"
            value={form.label}
            required
            onChange={(e) => setForm({ ...form, label: e.target.value })}
          />
          <input
            className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="Line 1"
            value={form.line1}
            required
            onChange={(e) => setForm({ ...form, line1: e.target.value })}
          />
          <input
            className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="City"
            value={form.city}
            required
            onChange={(e) => setForm({ ...form, city: e.target.value })}
          />
          <input
            className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="State"
            value={form.state}
            required
            onChange={(e) => setForm({ ...form, state: e.target.value })}
          />
          <input
            className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            placeholder="Postal code"
            value={form.postal_code}
            required
            onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
          />
          <label className="flex items-center gap-2 text-xs text-zinc-600">
            <input
              type="checkbox"
              checked={form.is_default}
              onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
            />
            Set as default
          </label>
          <button
            type="submit"
            className="md:col-span-2 rounded-2xl bg-orange-500 py-2 text-sm font-semibold text-white hover:bg-orange-600"
          >
            Save address
          </button>
        </form>
      </div>
    </div>
  );
}
