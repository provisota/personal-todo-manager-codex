import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';
import { LoginPage } from './LoginPage';
import { TodoAppPage } from './TodoAppPage';

export function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <main className="screen-center">
        <div className="loader" />
      </main>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/app" replace /> : <LoginPage />} />
      <Route path="/app/lists/:listId" element={user ? <TodoAppPage /> : <Navigate to="/login" replace />} />
      <Route path="/app/*" element={user ? <TodoAppPage /> : <Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to={user ? '/app' : '/login'} replace />} />
    </Routes>
  );
}
