# Frontend Codebase Analysis - Quick Reference

## 🎯 Project Overview

**Framework:** Next.js 15.3.1 (App Router)  
**Language:** TypeScript  
**Styling:** Tailwind CSS 4.x  
**State Management:** React Query (TanStack), Zustand  
**UI Library:** shadcn/ui (Radix UI primitives)  
**Authentication:** Supabase Auth  

---

## 📁 High-Level Structure Map

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   ├── components/             # Reusable React components
│   ├── hooks/                  # Custom React hooks
│   ├── lib/                    # Utility functions & configs
│   ├── contexts/               # React Context providers
│   └── providers/              # App-level providers
├── public/                     # Static assets
└── [config files]              # TypeScript, Tailwind, etc.
```

---

## 🔍 5-Minute Navigation Guide

### Where to Find Specific Features

| Feature | Location | Key Files |
|---------|----------|-----------|
| **Homepage** | `app/(home)/page.tsx` | Hero, pricing, features sections |
| **Dashboard** | `app/(dashboard)/dashboard/page.tsx` | Main app landing after auth |
| **Agent Chat/Thread** | `app/(dashboard)/projects/[projectId]/thread/[threadId]/` | AI conversation interface |
| **Agent Management** | `app/(dashboard)/agents/page.tsx` | Create/manage AI agents |
| **Settings** | `app/(dashboard)/settings/` | Billing, API keys, credentials |
| **Authentication** | `app/auth/` | Login, signup, OAuth callbacks |

---

## 🗂️ Critical Directory Breakdown

### `/src/app` - Routes & Pages

```
app/
├── (dashboard)/          # Authenticated app routes (layout wrapper)
│   ├── agents/          # Agent management & chat
│   ├── projects/        # Project-based thread view
│   ├── settings/        # User settings, billing
│   └── dashboard/       # Main dashboard
├── (home)/              # Public marketing pages
│   ├── page.tsx         # Landing page
│   └── changelog/       # Product updates
├── auth/                # Authentication flows
├── api/                 # API route handlers
│   ├── export/          # Document export (DOCX)
│   ├── integrations/    # OAuth callbacks
│   └── webhooks/        # Webhook handlers
└── [root files]         # Layout, globals, providers
```

**Route Groups Explained:**
- `(dashboard)` - Shared auth layout for app
- `(home)` - Public marketing layout
- `(personalAccount)` - Personal settings routes
- `(teamAccount)` - Team-specific routes

---

### `/src/components` - UI Components

```
components/
├── ui/                  # shadcn/ui base components (Button, Card, etc.)
├── agents/              # Agent-specific features
│   ├── config/          # Agent configuration UI
│   ├── composio/        # Integration management
│   ├── mcp/             # MCP server configuration
│   └── workflows/       # Workflow builder
├── thread/              # Chat/conversation UI
│   ├── chat-input/      # Message input, file upload
│   ├── content/         # Message rendering
│   └── tool-views/      # Tool result renderers
├── billing/             # Payment & subscription UI
├── dashboard/           # Dashboard-specific components
└── [feature folders]/   # Organized by feature
```

**Component Organization Pattern:**
- **Base UI:** `components/ui/` (shadcn)
- **Feature Components:** `components/[feature-name]/`
- **Shared Layouts:** `components/sidebar/`, `components/dashboard/`

---

### `/src/hooks` - Custom React Hooks

```
hooks/
├── react-query/         # React Query hooks (API data fetching)
│   ├── agents/          # Agent CRUD operations
│   ├── threads/         # Thread/message queries
│   ├── billing/         # Subscription & credits
│   └── [feature]/       # Feature-specific queries
├── use-accounts.ts      # Account management
├── use-model-selection.ts # AI model selection
└── use-mobile.ts        # Responsive utilities
```

**Key Hook Categories:**
- **Data Fetching:** React Query hooks in `react-query/`
- **Local State:** Zustand stores in `lib/stores/`
- **UI State:** Component-level hooks like `use-mobile.ts`

---

### `/src/lib` - Utilities & Configuration

```
lib/
├── api-client.ts        # Backend API wrapper
├── config.ts            # Environment configs
├── utils.ts             # Helper functions (cn, formatters)
├── supabase/            # Supabase client setup
│   ├── client.ts        # Browser client
│   └── server.ts        # Server-side client
├── stores/              # Zustand state stores
│   ├── agent-selection-store.ts
│   └── model-store.ts
└── actions/             # Server Actions
```

---

## 🔐 Authentication Flow

### Files Involved:
1. **`app/auth/page.tsx`** - Login/signup page
2. **`app/auth/callback/route.ts`** - OAuth callback handler
3. **`components/AuthProvider.tsx`** - Auth context wrapper
4. **`src/middleware.ts`** - Route protection

### Auth Check Process:
```typescript
// middleware.ts protects routes
PUBLIC_ROUTES -> Allow access
BILLING_ROUTES -> Check subscription status
PROTECTED_ROUTES -> Require active session + billing check
```

---

## 💬 Thread/Chat System Architecture

### Core Components:

```
Thread View (projects/[projectId]/thread/[threadId]/)
├── page.tsx                    # Main thread page
├── _components/
│   ├── ThreadLayout.tsx        # Layout wrapper
│   └── ThreadError.tsx         # Error states
├── _hooks/
│   ├── useThreadData.ts        # Load messages/project
│   ├── useToolCalls.ts         # Parse & display tool usage
│   └── useBilling.ts           # Check usage limits
└── _types/
    └── index.ts                # TypeScript types
```

### Data Flow:
1. **Load Thread Data:** `useThreadData` → Fetch messages, project info
2. **Parse Tool Calls:** `useToolCalls` → Extract tool usage from messages
3. **Render Messages:** `ThreadComponent` → Display conversation
4. **Side Panel:** Tool call details with navigation

---

## 🛠️ Agent Configuration System

### Key Files:
```
agents/config/[agentId]/
├── workflow/
│   └── [workflowId]/
│       └── page.tsx           # Workflow builder

components/agents/
├── agent-configuration-dialog.tsx  # Main config modal
├── config/
│   ├── configuration-tab.tsx      # Settings tab
│   └── model-selector.tsx         # AI model picker
├── workflows/
│   └── conditional-workflow-builder.tsx  # Visual workflow editor
└── tools/
    └── granular-tool-configuration.tsx   # Tool permissions
```

### Configuration Flow:
1. Select agent → Open config dialog
2. Configure: System prompt, tools, model, workflows
3. Save → Backend API updates agent settings

---

## 💳 Billing & Subscription System

### Components:
```
components/billing/
├── billing-modal.tsx           # Stripe checkout modal
├── credit-balance-card.tsx     # Credit display
├── credit-purchase.tsx         # Buy more credits
└── usage-limit-alert.tsx       # Over-limit warnings

hooks/react-query/billing/
├── use-billing-v2.ts           # Main billing queries
├── use-trial-status.ts         # Trial state management
└── use-transactions.ts         # Usage history
```

### Billing Check Logic:
```typescript
// middleware.ts
if (!hasTier && !hasActiveTrial) {
  -> redirect to /activate-trial or /subscription
}

// In-app checks
useBillingStatusQuery() -> Check before agent runs
```

---

## 🔌 API Integration Pattern

### Backend Communication:

```typescript
// lib/api-client.ts
export const backendApi = {
  get: (path) => fetch(`${BACKEND_URL}/api${path}`),
  post: (path, body) => fetch(/* ... */),
  // ... CRUD operations
}

// Usage in React Query:
const { data } = useQuery({
  queryKey: ['agents', agentId],
  queryFn: () => backendApi.get(`/agents/${agentId}`)
})
```

### API Route Handlers:
- **`app/api/export/docx/`** - Server-side DOCX generation
- **`app/api/integrations/[provider]/callback/`** - OAuth redirects
- **`app/api/edge-flags/`** - Feature flags (Vercel Edge Config)

---

## 🎨 Styling System

### Tailwind Configuration:
```typescript
// tailwind.config.js (conceptual - using v4)
- Custom colors via CSS variables (--primary, --secondary, etc.)
- Dark mode support with `.dark` class
- Custom animations in globals.css
```

### Theme Variables (`app/globals.css`):
```css
:root {
  --background: oklch(0.9741 0 129.63);
  --primary: oklch(0.205 0 0);
  --secondary: oklch(54.65% 0.246 262.87);
  /* ... more color tokens */
}

.dark {
  --background: oklch(0.185 0.005 285.823);
  /* ... dark theme overrides */
}
```

---

## 🔄 State Management Overview

### React Query (Server State):
```typescript
// hooks/react-query/agents/use-agents.ts
export const useAgents = (params: AgentsParams) => {
  return useQuery({
    queryKey: ['agents', params],
    queryFn: () => backendApi.get('/agents', params)
  })
}
```

### Zustand (Client State):
```typescript
// lib/stores/model-store.ts
export const useModelStore = create<ModelStore>((set) => ({
  selectedModel: null,
  setSelectedModel: (model) => set({ selectedModel: model })
}))
```

### React Context (UI State):
```typescript
// contexts/BillingContext.tsx
export const BillingContext = createContext<BillingContextType>(...)
```

---

## 📦 Key Dependencies

| Package | Purpose | Usage Example |
|---------|---------|---------------|
| **@tanstack/react-query** | Server state management | `useQuery`, `useMutation` |
| **@supabase/ssr** | Auth & database | `createClient()` |
| **@radix-ui/react-*** | Headless UI primitives | Dialog, Dropdown, etc. |
| **framer-motion** | Animations | Page transitions, reveals |
| **zod** | Schema validation | Form validation, API parsing |
| **zustand** | Client state store | Global UI state |
| **sonner** | Toast notifications | `toast.success()`, `toast.error()` |
| **lucide-react** | Icon library | `<Check />`, `<Zap />` |

---

## 🚀 Quick Start Development

### Running Locally:
```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Fill in required vars:
# - NEXT_PUBLIC_SUPABASE_URL
# - NEXT_PUBLIC_SUPABASE_ANON_KEY
# - NEXT_PUBLIC_BACKEND_URL

# Start dev server
npm run dev
```

### Environment Variables:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api
NEXT_PUBLIC_URL=http://localhost:3000
NEXT_PUBLIC_ENV_MODE=LOCAL  # Disables billing checks
```

---

## 🔍 Code Navigation Shortcuts

### Find Feature Implementations:

**Search Strategy:**
1. **Find Route:** Search `app/` for page filename
2. **Find Component:** Search `components/[feature]/`
3. **Find Data Hook:** Search `hooks/react-query/[feature]/`
4. **Find API Call:** Search `lib/api-client.ts` or `hooks/react-query/`

**VS Code Shortcuts:**
- `Ctrl/Cmd + P` → Quick file search
- `Ctrl/Cmd + Shift + F` → Search in all files
- `F12` → Go to definition
- `Shift + F12` → Find all references

---

## 📊 Common Patterns in This Codebase

### 1. Page Component Pattern:
```typescript
// app/feature/page.tsx
'use client';  // Client component

export default function FeaturePage() {
  const { data, isLoading } = useFeatureQuery();
  
  if (isLoading) return <Skeleton />;
  
  return <FeatureContent data={data} />;
}
```

### 2. Data Fetching Pattern:
```typescript
// hooks/react-query/feature/use-feature.ts
export const useFeature = (id: string) => {
  return useQuery({
    queryKey: ['feature', id],
    queryFn: async () => {
      const response = await backendApi.get(`/feature/${id}`);
      return response.data;
    }
  });
};
```

### 3. Form Handling Pattern:
```typescript
// Using react-hook-form + zod
const form = useForm<FormData>({
  resolver: zodResolver(schema)
});

const onSubmit = async (data: FormData) => {
  await mutation.mutateAsync(data);
  toast.success('Saved!');
};
```

### 4. Protected Route Pattern:
```typescript
// middleware.ts checks auth
// Component assumes user is authenticated
const { user } = useAuth();  // Never null in protected routes
```

---

## 🐛 Debugging Tips

### Common Issues & Solutions:

**Issue:** "Failed to fetch" errors  
**Solution:** Check `NEXT_PUBLIC_BACKEND_URL` in `.env.local`

**Issue:** Authentication redirects loop  
**Solution:** Clear cookies, check middleware route patterns

**Issue:** Billing checks blocking access  
**Solution:** Set `NEXT_PUBLIC_ENV_MODE=LOCAL` to bypass

**Issue:** TypeScript errors after changes  
**Solution:** Restart TS server (`Cmd/Ctrl + Shift + P` → "TypeScript: Restart TS Server")

### Debug Mode:
```typescript
// Thread component has debug mode
// Add ?debug=true to URL to see internal state
const debugMode = searchParams.get('debug') === 'true';
```

---

## 📝 Code Style Guidelines

### File Naming:
- **Components:** PascalCase (`AgentCard.tsx`)
- **Hooks:** camelCase with `use` prefix (`useAgents.ts`)
- **Utilities:** kebab-case (`api-client.ts`)
- **Types:** PascalCase interfaces (`AgentConfig`)

### Import Order:
```typescript
// 1. React/Next.js
import { useState } from 'react';
import { useRouter } from 'next/navigation';

// 2. External packages
import { useQuery } from '@tanstack/react-query';

// 3. Internal components
import { Button } from '@/components/ui/button';

// 4. Hooks & utilities
import { useAgents } from '@/hooks/react-query/agents/use-agents';

// 5. Types
import type { Agent } from '@/lib/api';
```

### Component Structure:
```typescript
'use client';  // If needed

// 1. Imports
import { ... } from '...';

// 2. Types/Interfaces
interface Props {
  // ...
}

// 3. Component
export default function MyComponent({ ... }: Props) {
  // 3a. Hooks
  const [state, setState] = useState();
  
  // 3b. Queries/Mutations
  const { data } = useQuery(...);
  
  // 3c. Effects
  useEffect(() => { ... }, []);
  
  // 3d. Handlers
  const handleClick = () => { ... };
  
  // 3e. Render
  return <div>...</div>;
}
```

---

## 🎯 Key Takeaways

### For Quick Understanding:
1. **App Router Structure:** Routes mirror URL structure in `app/`
2. **Data Fetching:** React Query hooks in `hooks/react-query/`
3. **UI Components:** shadcn/ui in `components/ui/`
4. **Authentication:** Supabase + middleware protection
5. **Billing:** Checked in middleware + in-app queries

### For Making Changes:
1. **Add Route:** Create `page.tsx` in `app/[route]/`
2. **Add Component:** Create in `components/[feature]/`
3. **Add Data Hook:** Create in `hooks/react-query/[feature]/`
4. **Add API Call:** Update `lib/api-client.ts` or create route handler
5. **Style:** Use Tailwind classes, check `globals.css` for theme vars

### For Debugging:
1. Check browser console for errors
2. Use React Query DevTools (imported in dev)
3. Check Network tab for API failures
4. Add `?debug=true` for debug mode (where supported)
5. Use VS Code's TypeScript checking

---

## 📚 Related Documentation

- **Next.js App Router:** https://nextjs.org/docs/app
- **React Query:** https://tanstack.com/query/latest
- **shadcn/ui:** https://ui.shadcn.com
- **Supabase Auth:** https://supabase.com/docs/guides/auth
- **Tailwind CSS:** https://tailwindcss.com/docs

---

**Last Updated:** Based on codebase snapshot  
**Framework Version:** Next.js 15.3.1, React 18, TypeScript 5