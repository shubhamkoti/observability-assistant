import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';

export default function Register() {
  const navigate = useNavigate();
  const { loginWithToken, user, loading } = useAuth();
  const [form, setForm] = useState({
    email: '',
    password: '',
    full_name: '',
    seller_shop_name: '',
  });
  const [busy, setBusy] = useState(false);

  if (loading) {
    return <div className="py-24 text-center text-sm text-zinc-500">Loading…</div>;
  }
  if (user) {
    return <Navigate to="/" replace />;
  }

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = {
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        seller_shop_name: form.seller_shop_name.trim() || null,
      };
      const res = await api.post('/auth/register', payload);
      await loginWithToken(res.data.access_token);
      toast.success('Account ready');
      navigate('/', { replace: true });
    } catch {
      toast.error('Could not register (email taken?)');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-lg space-y-6 rounded-3xl border border-zinc-200 bg-white p-8 shadow-sm">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Create account</h1>
        <p className="mt-2 text-sm text-zinc-500">Optional seller shop name grants seller + customer roles.</p>
      </div>
      <form className="grid gap-3" onSubmit={submit}>
        <input
          className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-orange-500/40"
          placeholder="Full name"
          value={form.full_name}
          required
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
        />
        <input
          className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-orange-500/40"
          type="email"
          placeholder="Email"
          value={form.email}
          required
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <input
          className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-orange-500/40"
          type="password"
          placeholder="Password (min 6 chars)"
          value={form.password}
          required
          minLength={6}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <input
          className="rounded-2xl border border-zinc-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-orange-500/40"
          placeholder="Seller shop name (optional)"
          value={form.seller_shop_name}
          onChange={(e) => setForm({ ...form, seller_shop_name: e.target.value })}
        />
        <button
          type="submit"
          disabled={busy || loading}
          className="rounded-2xl bg-orange-500 py-2.5 text-sm font-semibold text-white hover:bg-orange-600 disabled:opacity-60"
        >
          {busy ? 'Creating…' : 'Register'}
        </button>
      </form>
      <p className="text-center text-sm text-zinc-500">
        Have an account?{' '}
        <Link className="font-semibold text-orange-600 hover:underline" to="/login">
          Sign in
        </Link>
      </p>
    </div>
  );
}
