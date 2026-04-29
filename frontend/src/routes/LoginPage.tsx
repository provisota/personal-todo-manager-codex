import { Github } from 'lucide-react';
import { useEffect, useState } from 'react';

import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import type { AuthProviders } from '../types/domain';

export function LoginPage() {
  const { testLogin, error } = useAuth();
  const [providers, setProviders] = useState<AuthProviders | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);

  useEffect(() => {
    api
      .providers()
      .then(setProviders)
      .catch(() => setLoginError('Backend is not reachable from this browser origin.'));
  }, []);

  async function runTestLogin() {
    setLoginError(null);
    try {
      await testLogin();
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'Local demo login is not available.');
    }
  }

  return (
    <main className="login-page">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="brand-mark">PT</div>
        <h1 id="login-title">Personal To-Do Manager</h1>
        <p>Plan projects, track priorities, and keep deadlines visible.</p>
        {error ? <div className="alert">Session check failed: {error}</div> : null}
        {loginError ? <div className="alert">{loginError}</div> : null}
        {providers?.google ? (
          <a className="oauth-button" href={api.loginUrl('google')}>
            <span className="google-dot">G</span>
            Continue with Google
          </a>
        ) : (
          <button className="oauth-button disabled" type="button" disabled title="Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env">
            <span className="google-dot">G</span>
            Google OAuth not configured
          </button>
        )}
        {providers?.github ? (
          <a className="oauth-button" href={api.loginUrl('github')}>
            <Github size={20} aria-hidden="true" />
            Continue with GitHub
          </a>
        ) : (
          <button className="oauth-button disabled" type="button" disabled title="Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in backend/.env">
            <Github size={20} aria-hidden="true" />
            GitHub OAuth not configured
          </button>
        )}
        {providers?.test_auth ? (
          <button className="ghost-button full-width" type="button" onClick={() => void runTestLogin()}>
            Use local demo login
          </button>
        ) : (
          <button className="ghost-button full-width" type="button" disabled title="Set TEST_AUTH_ENABLED=true in backend/.env">
            Local demo login disabled
          </button>
        )}
        <div className="login-hint">
          OAuth buttons become active after provider credentials are added to backend configuration.
        </div>
      </section>
    </main>
  );
}
