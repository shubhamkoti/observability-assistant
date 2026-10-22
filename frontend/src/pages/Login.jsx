import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';

export default function Login() {
  const navigate = useNavigate();
  const { loginWithToken, user, loading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
      const res = await api.post('/auth/login', { email, password });
      await loginWithToken(res.data.access_token);
      toast.success('Welcome back!');
      navigate('/', { replace: true });
    } catch {
      toast.error('Invalid credentials');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-md space-y-6 rounded-3xl border border-zinc-200 bg-white p-8 shadow-sm">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Sign in</h1>
        <p className="mt-2 text-sm text-zinc-500">Demo: buyer@example.com / Buyer123!</p>
      </div>
      <form className="space-y-4" onSubmit={submit}>
        <div>
          <label className="text-xs font-medium text-zinc-600">Email</label>
          <input
            className="mt-1 w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-orange-500/40"
            type="email"
            value={email}
            required
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-zinc-600">Password</label>
          <input
            className="mt-1 w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-orange-500/40"
            type="password"
            value={password}
            required
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={busy || loading}
          className="w-full rounded-2xl bg-orange-500 py-2.5 text-sm font-semibold text-white shadow hover:bg-orange-600 disabled:opacity-60"
        >
          {busy ? 'Signing in…' : 'Continue'}
        </button>
      </form>
      <p className="text-center text-sm text-zinc-500">
        New here?{' '}
        <Link className="font-semibold text-orange-600 hover:underline" to="/register">
          Create account
        </Link>
      </p>
    </div>
  );
}
