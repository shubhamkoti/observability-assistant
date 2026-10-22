import { useState } from 'react';
import toast from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';

export default function Support() {
  const { user } = useAuth();
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  const send = async (e) => {
    e.preventDefault();
    if (!user) {
      toast.error('Sign in to send a message');
      return;
    }
    setBusy(true);
    try {
      const res = await api.post('/support/', { message });
      toast.success(res.data.detail || 'Stored in MongoDB chat_support_messages');
      setMessage('');
    } catch {
      toast.error('Could not send');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl space-y-6 rounded-3xl border border-zinc-200 bg-white p-8 shadow-sm">
      <div>
        <h1 className="text-2xl font-bold">Support chat (simulated)</h1>
        <p className="mt-2 text-sm text-zinc-500">
          Messages are persisted in MongoDB collection <code className="rounded bg-zinc-100 px-1">chat_support_messages</code>.
        </p>
      </div>
      {!user && (
        <p className="text-sm text-orange-800">
          Please <Link className="underline" to="/login">sign in</Link> first.
        </p>
      )}
      <form className="space-y-3" onSubmit={send}>
        <textarea
          className="w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
          rows={4}
          placeholder="How can we help?"
          value={message}
          required
          disabled={!user}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button
          type="submit"
          disabled={!user || busy}
          className="rounded-2xl bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-800 disabled:opacity-40"
        >
          {busy ? 'Sending…' : 'Send'}
        </button>
      </form>
    </div>
  );
}
