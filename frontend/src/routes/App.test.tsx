import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AuthProvider } from '../auth/AuthContext';
import { App } from './App';

class MockWebSocket {
  static OPEN = 1;
  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;

  send() {}

  close() {
    this.onclose?.();
  }
}

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn()
    });
    vi.stubGlobal('WebSocket', MockWebSocket);
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith('/auth/me')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                id: 'user-1',
                email: 'user@example.com',
                display_name: 'User One',
                avatar_url: null
              })
          });
        }
        if (url.endsWith('/api/lists')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve([])
          });
        }
        return Promise.resolve({
          ok: false,
          status: 404,
          json: () => Promise.resolve({ detail: { message: 'Not found' } })
        });
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the authenticated app and empty list state', async () => {
    render(
      <MemoryRouter initialEntries={['/app']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('No list selected')).toBeInTheDocument();
    expect(await screen.findByText(/no lists yet/i)).toBeInTheDocument();
  });
});
