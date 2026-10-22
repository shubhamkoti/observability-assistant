import { Link, NavLink, Outlet } from 'react-router-dom';
import { ShoppingCartIcon, BoltIcon } from './icons.jsx';
import { useAuth } from '../context/AuthContext.jsx';

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `rounded-full px-3 py-2 text-sm font-medium transition hover:bg-orange-500/15 ${
          isActive ? 'bg-orange-500/25 text-orange-900' : 'text-zinc-700'
        }`
      }
    >
      {children}
    </NavLink>
  );
}

export default function Layout() {
  const { user, logout, hasRole } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white shadow-sm backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight text-lg">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500 to-amber-400 text-white shadow">
              <BoltIcon />
            </span>
            <span>MarketGrid</span>
          </Link>
          <nav className="hidden flex-1 items-center gap-1 md:flex">
            <NavItem to="/">Shop</NavItem>
            <NavItem to="/cart">Cart</NavItem>
            <NavItem to="/wishlist">Wishlist</NavItem>
            <NavItem to="/orders">Orders</NavItem>
            <NavItem to="/profile">Profile</NavItem>
            <NavItem to="/support">Support</NavItem>
            {hasRole('seller') && <NavItem to="/seller">Seller</NavItem>}
            {hasRole('admin') && <NavItem to="/admin">Admin</NavItem>}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <Link
              to="/cart"
              className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm font-medium text-zinc-800 hover:border-orange-300"
            >
              <ShoppingCartIcon />
              <span className="hidden sm:inline">Cart</span>
            </Link>
            {user ? (
              <button
                type="button"
                onClick={logout}
                className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-zinc-800"
              >
                Logout
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/register"
                  className="hidden rounded-full border border-zinc-200 px-3 py-2 text-sm font-medium text-zinc-800 hover:bg-zinc-50 sm:inline"
                >
                  Sign up
                </Link>
                <Link
                  to="/login"
                  className="rounded-full bg-orange-500 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-orange-600"
                >
                  Sign in
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
        <Outlet />
      </main>
      <footer className="border-t bg-white py-6 text-center text-xs text-zinc-500">
        MarketGrid — DBMS coursework showcase · PostgreSQL + MongoDB + FastAPI + React
      </footer>
    </div>
  );
}
