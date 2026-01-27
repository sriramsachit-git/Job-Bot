import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../App'

// Create a test QueryClient
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

describe('App', () => {
  it('renders without crashing', () => {
    const queryClient = createTestQueryClient()
    
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    )
    
    // Basic smoke test - if this passes, the app renders
    expect(document.body).toBeTruthy()
  })
})
