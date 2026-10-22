import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';

export default function Product() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [p, setP] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [qty, setQty] = useState(1);
  const [review, setReview] = useState({ rating: 5, title: '', body: '' });

  useEffect(() => {
    api
      .get(`/products/${id}`)
      .then((r) => setP(r.data))
      .catch(() => toast.error('Failed to load product'));
    api
      .get(`/reviews/product/${id}`)
      .then((r) => setReviews(r.data))
      .catch(() => {});
  }, [id]);

  const addCart = async () => {
    if (!user) {
      toast.error('Sign in to add items');
      navigate('/login');
      return;
    }
    try {
      await api.post('/cart/', { product_id: Number(id), quantity: qty });
      toast.success('Added to cart');
    } catch {
      toast.error('Could not update cart');
    }
  };

  const toggleWishlist = async () => {
    if (!user) {
      navigate('/login');
      return;
    }
    try {
      await api.post(`/wishlist/${id}`);
      toast.success('Saved to wishlist');
    } catch {
      toast.message('Wishlist updated');
    }
  };

  const submitReview = async (e) => {
    e.preventDefault();
    if (!user) {
      navigate('/login');
      return;
    }
    try {
      await api.post(`/reviews/product/${id}`, review);
      toast.success('Review posted');
      const r = await api.get(`/reviews/product/${id}`);
      setReviews(r.data);
      setReview({ rating: 5, title: '', body: '' });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Review not allowed yet';
      toast.error(msg);
    }
  };

  if (!p) {
    return <div className="py-24 text-center text-sm text-zinc-500">Loading…</div>;
  }

  return (
    <div className="grid gap-10 md:grid-cols-[1.05fr_0.95fr]">
      <div className="space-y-4">
        <div className="aspect-[4/3] w-full rounded-3xl bg-gradient-to-br from-zinc-100 to-orange-50 shadow-inner" />
        <div className="rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-orange-700">SKU {p.sku || '—'}</p>
          <h1 className="mt-2 text-3xl font-bold">{p.name}</h1>
          <p className="mt-4 text-lg font-semibold text-orange-600">${Number(p.price).toFixed(2)}</p>
          {p.compare_at_price && (
            <p className="text-sm text-zinc-400 line-through">${Number(p.compare_at_price).toFixed(2)}</p>
          )}
          <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-zinc-700">{p.description}</p>
          <p className="mt-3 text-sm text-zinc-500">
            Stock: <span className="font-semibold text-zinc-900">{p.stock}</span> · Avg rating:{' '}
            {p.avg_rating != null ? p.avg_rating.toFixed(1) : '—'}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <input
              type="number"
              min={1}
              value={qty}
              onChange={(e) => setQty(Math.max(1, Number(e.target.value)))}
              className="w-24 rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={addCart}
              className="rounded-2xl bg-orange-500 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-orange-600"
            >
              Add to cart
            </button>
            <button
              type="button"
              onClick={toggleWishlist}
              className="rounded-2xl border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-50"
            >
              Wishlist
            </button>
          </div>
        </div>
      </div>
      <div className="space-y-4">
        <div className="rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Reviews</h2>
          <ul className="mt-4 space-y-3">
            {reviews.map((rv) => (
              <li key={rv.id} className="rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-2 text-sm">
                <div className="flex justify-between gap-2">
                  <span className="font-semibold">{rv.title}</span>
                  <span className="text-orange-700">{rv.rating}★</span>
                </div>
                {rv.body && <p className="mt-1 text-xs text-zinc-600">{rv.body}</p>}
              </li>
            ))}
            {reviews.length === 0 && <li className="text-xs text-zinc-400">No reviews yet.</li>}
          </ul>
          {user && (
            <form className="mt-6 space-y-2 border-t border-zinc-100 pt-4" onSubmit={submitReview}>
              <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Write a review</p>
              <select
                className="w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
                value={review.rating}
                onChange={(e) => setReview({ ...review, rating: Number(e.target.value) })}
              >
                {[5, 4, 3, 2, 1].map((x) => (
                  <option key={x} value={x}>
                    {x} stars
                  </option>
                ))}
              </select>
              <input
                className="w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
                placeholder="Title"
                value={review.title}
                required
                onChange={(e) => setReview({ ...review, title: e.target.value })}
              />
              <textarea
                className="w-full rounded-2xl border border-zinc-200 px-3 py-2 text-sm"
                placeholder="Thoughts…"
                rows={3}
                value={review.body}
                onChange={(e) => setReview({ ...review, body: e.target.value })}
              />
              <button
                type="submit"
                className="rounded-2xl bg-zinc-900 px-4 py-2 text-sm font-semibold text-white hover:bg-zinc-800"
              >
                Submit
              </button>
            </form>
          )}
          {!user && <p className="mt-4 text-xs text-zinc-500">Sign in to leave a review.</p>}
        </div>
      </div>
    </div>
  );
}
