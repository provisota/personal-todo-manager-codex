import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AuthProvider } from '../auth/AuthContext';
import { LoginPage } from './LoginPage';

const fetchMock = vi.fn((input: RequestInfo | URL) => {
  const url = String(input);
  if (url.endsWith('/auth/providers')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ google: true, github: true, test_auth: true })
    });
  }
  return Promise.resolve({
    ok: false,
    status: 401,
    json: () => Promise.resolve({ detail: 'Unauthorized' })
  });
});

vi.stubGlobal('fetch', fetchMock);

describe('LoginPage', () => {
  beforeEach(() => {
    fetchMock.mockClear();
  });

  it('renders both SSO provider actions', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByRole('link', { name: /continue with google/i })).toBeInTheDocument();
    expect(await screen.findByRole('link', { name: /continue with github/i })).toBeInTheDocument();
  });
});
