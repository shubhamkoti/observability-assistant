import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import { useAuth } from './context/AuthContext.jsx';
import Home from './pages/Home.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Product from './pages/Product.jsx';
import Cart from './pages/Cart.jsx';
import Checkout from './pages/Checkout.jsx';
import Orders from './pages/Orders.jsx';
import Wishlist from './pages/Wishlist.jsx';
import Profile from './pages/Profile.jsx';
import Admin from './pages/Admin.jsx';
import Seller from './pages/Seller.jsx';
import Support from './pages/Support.jsx';

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="py-24 text-center text-sm text-zinc-500">Loading session…</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function RoleGate({ role, children }) {
  const { user, loading, hasRole } = useAuth();
  if (loading) {
    return <div className="py-24 text-center text-sm text-zinc-500">Loading session…</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (!hasRole(role)) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="/products/:id" element={<Product />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/support" element={<Support />} />
        <Route
          path="/cart"
          element={
            <Protected>
              <Cart />
            </Protected>
          }
        />
        <Route
          path="/checkout"
          element={
            <Protected>
              <Checkout />
            </Protected>
          }
        />
        <Route
          path="/orders"
          element={
            <Protected>
              <Orders />
            </Protected>
          }
        />
        <Route
          path="/wishlist"
          element={
            <Protected>
              <Wishlist />
            </Protected>
          }
        />
        <Route
          path="/profile"
          element={
            <Protected>
              <Profile />
            </Protected>
          }
        />
        <Route
          path="/admin"
          element={
            <RoleGate role="admin">
              <Admin />
            </RoleGate>
          }
        />
        <Route
          path="/seller"
          element={
            <RoleGate role="seller">
              <Seller />
            </RoleGate>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
