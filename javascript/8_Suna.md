# Complete Guide to Understanding the Suna Project Structure

## Table of Contents
1. [Project Overview](#project-overview)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [Frontend Deep Dive](#frontend-deep-dive)
4. [Backend Deep Dive](#backend-deep-dive)
5. [Mobile App Structure](#mobile-app-structure)
6. [SDK and Integration](#sdk-and-integration)
7. [How to Connect Frontend to Backend](#how-to-connect-frontend-to-backend)
8. [Building Production-Ready Features](#building-production-ready-features)

---

## Project Overview

Suna is a **full-stack AI agent platform** with:
- **Frontend**: Next.js 13+ with App Router (TypeScript/React)
- **Backend**: Python FastAPI
- **Mobile**: React Native (Expo)
- **SDK**: Python SDK for developers
- **Database**: Supabase (PostgreSQL)

### Monorepo Structure
```
suna/
├── frontend/          # Next.js web application
├── backend/           # FastAPI Python server
├── apps/mobile/       # React Native mobile app
├── sdk/              # Python SDK
└── docs/             # Documentation
```

---

## Understanding the Architecture

### The Big Picture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   Backend    │─────▶│  Supabase   │
│  (Next.js)  │◀─────│  (FastAPI)   │◀─────│ (Database)  │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     │
       │                     │
       ▼                     ▼
┌─────────────┐      ┌──────────────┐
│   Mobile    │      │   Docker     │
│   (Expo)    │      │  (Sandboxes) │
└─────────────┘      └──────────────┘
```

### Key Concepts

**Monolithic Frontend**: The `frontend/` directory contains ALL web UI code
**API-First Backend**: The `backend/` directory exposes REST APIs
**Shared Types**: TypeScript types are defined per-module
**Real-time Updates**: Supabase handles WebSocket subscriptions

---

## Frontend Deep Dive

### Directory Structure Explanation

```
frontend/
├── src/
│   ├── app/              # Next.js App Router (pages & routing)
│   ├── components/       # Reusable React components
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utilities & helpers
│   ├── contexts/        # React Context providers
│   └── providers/       # Top-level providers
├── public/              # Static assets (images, fonts)
└── scripts/             # Build/maintenance scripts
```

### Understanding Next.js App Router

#### What is `app/`?

The `app/` directory in Next.js 13+ uses **file-based routing**:

```
app/
├── layout.tsx           # Root layout (wraps all pages)
├── page.tsx            # Homepage (/)
├── (dashboard)/        # Route group (doesn't affect URL)
│   ├── layout.tsx      # Dashboard layout
│   └── agents/         
│       └── page.tsx    # /agents page
└── api/                # API routes (backend-for-frontend)
    └── edge-flags/
        └── route.ts    # /api/edge-flags endpoint
```

#### Identifying Pages vs Components

**Pages** (routes):
- Located in `app/` directory
- Named `page.tsx` or `layout.tsx`
- Automatically become routes
- Example: `app/agents/page.tsx` → `/agents`

**Components** (reusable UI):
- Located in `components/` directory
- Can be named anything (e.g., `Button.tsx`)
- Imported and used in pages
- Example: `components/ui/button.tsx`

#### Route Groups

Folders in `()` are **route groups** - they organize code without affecting URLs:

```
app/
├── (dashboard)/        # Not in URL
│   └── agents/
│       └── page.tsx    # URL: /agents (NOT /dashboard/agents)
└── (home)/            # Not in URL
    └── page.tsx        # URL: / (homepage)
```

#### Dynamic Routes

Folders in `[]` create **dynamic segments**:

```
app/
└── agents/
    └── [threadId]/     # Dynamic parameter
        └── page.tsx    # URL: /agents/123 (threadId = "123")
```

In the page component:
```typescript
export default function ThreadPage({ 
  params 
}: { 
  params: { threadId: string } 
}) {
  const { threadId } = params; // Access the dynamic value
  return <div>Thread: {threadId}</div>;
}
```

### Understanding Key Folders

#### 1. `components/` - Reusable UI

```
components/
├── ui/                  # Base UI components (shadcn/ui)
│   ├── button.tsx      # Generic button
│   ├── dialog.tsx      # Modal dialogs
│   └── card.tsx        # Card containers
├── agents/             # Agent-specific components
│   ├── agent-card.tsx  # Display agent info
│   └── agent-configuration-dialog.tsx
├── thread/             # Chat/conversation components
│   ├── chat-input.tsx  # Message input box
│   └── ThreadComponent.tsx
└── billing/            # Payment components
    └── credit-purchase.tsx
```

**Pattern**: Components are grouped by feature/domain

#### 2. `hooks/` - Custom React Hooks

Hooks are **reusable logic** extracted from components:

```typescript
// hooks/use-agent-version-data.ts
export function useAgentVersionData(agentId: string) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => fetchAgent(agentId),
  });
  
  return { agent: data, isLoading, error };
}
```

Usage in a component:
```typescript
function AgentPage({ agentId }: { agentId: string }) {
  const { agent, isLoading } = useAgentVersionData(agentId);
  
  if (isLoading) return <Skeleton />;
  return <div>{agent.name}</div>;
}
```

**When to use hooks:**
- Fetching data (React Query)
- Managing state (useState, useReducer)
- Side effects (useEffect)
- Reusable logic across components

#### 3. `lib/` - Utilities & Configuration

```
lib/
├── api-client.ts       # HTTP client for backend
├── utils.ts           # Helper functions
├── supabase/          # Supabase client
│   ├── client.ts      # Browser client
│   └── server.ts      # Server-side client
└── stores/            # Zustand stores (state management)
    └── agent-selection-store.ts
```

**Example: API Client**
```typescript
// lib/api-client.ts
export async function apiFetch(endpoint: string, options?: RequestInit) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) throw new Error('API request failed');
  return response.json();
}
```

#### 4. `contexts/` - React Context

Context shares data across components without prop drilling:

```typescript
// contexts/BillingContext.tsx
const BillingContext = createContext<BillingData | null>(null);

export function BillingProvider({ children }: { children: ReactNode }) {
  const [credits, setCredits] = useState(0);
  
  return (
    <BillingContext.Provider value={{ credits, setCredits }}>
      {children}
    </BillingContext.Provider>
  );
}

export function useBilling() {
  const context = useContext(BillingContext);
  if (!context) throw new Error('useBilling must be used within BillingProvider');
  return context;
}
```

#### 5. `providers/` - Top-Level Wrappers

```typescript
// providers/react-query-provider.tsx
export function ReactQueryProvider({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient();
  
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

Used in `app/layout.tsx`:
```typescript
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html>
      <body>
        <ReactQueryProvider>
          <BillingProvider>
            {children}
          </BillingProvider>
        </ReactQueryProvider>
      </body>
    </html>
  );
}
```

### Understanding Routing in Detail

#### File-Based Routing

Next.js automatically creates routes from files:

| File Path | URL | Purpose |
|-----------|-----|---------|
| `app/page.tsx` | `/` | Homepage |
| `app/agents/page.tsx` | `/agents` | Agents list |
| `app/agents/[id]/page.tsx` | `/agents/123` | Single agent |
| `app/api/users/route.ts` | `/api/users` | API endpoint |

#### Layouts

Layouts wrap pages and persist across navigation:

```typescript
// app/(dashboard)/layout.tsx
export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="dashboard">
      <Sidebar />
      <main>{children}</main>
    </div>
  );
}
```

This layout wraps ALL pages in `(dashboard)/`:
- `/agents` → Sidebar + AgentsPage
- `/settings` → Sidebar + SettingsPage

#### Navigation

```typescript
import { useRouter } from 'next/navigation';
import Link from 'next/link';

function MyComponent() {
  const router = useRouter();
  
  // Programmatic navigation
  const handleClick = () => {
    router.push('/agents/123');
  };
  
  return (
    <>
      {/* Declarative navigation */}
      <Link href="/agents">Go to Agents</Link>
      
      {/* Programmatic */}
      <button onClick={handleClick}>View Agent</button>
    </>
  );
}
```

### Understanding `public/` Folder

```
public/
├── images/          # Static images
│   ├── logo.png
│   └── banner.jpg
├── fonts/          # Custom fonts (if not using Google Fonts)
└── favicon.ico     # Browser tab icon
```

**Usage in code:**
```typescript
// Images
<img src="/images/logo.png" alt="Logo" />

// Next.js Image component (optimized)
import Image from 'next/image';
<Image src="/images/logo.png" width={200} height={100} alt="Logo" />
```

### Understanding Authentication

#### Where Auth Happens

```
app/
├── auth/
│   ├── page.tsx         # Login/signup page
│   ├── actions.ts       # Server actions (form submission)
│   └── callback/
│       └── route.ts     # OAuth callback handler
└── components/
    └── AuthProvider.tsx # Client-side auth wrapper
```

#### Auth Flow

1. **User visits protected route** → Redirected to `/auth`
2. **User submits login form** → `actions.ts` calls Supabase
3. **Supabase returns session** → Token stored in cookies
4. **Redirect to dashboard** → Session validated on each request

**Example: Protected Page**
```typescript
// app/agents/page.tsx
import { createClient } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';

export default async function AgentsPage() {
  const supabase = createClient();
  const { data: { user } } = await supabase.auth.getUser();
  
  if (!user) redirect('/auth');
  
  return <div>Welcome {user.email}</div>;
}
```

### Understanding API Routes

API routes in `app/api/` act as a **Backend-for-Frontend (BFF)**:

```
app/api/
├── edge-flags/
│   └── route.ts        # GET /api/edge-flags
└── webhooks/
    └── trigger/
        └── [workflowId]/
            └── route.ts # POST /api/webhooks/trigger/:workflowId
```

**Example: API Route**
```typescript
// app/api/edge-flags/route.ts
export async function GET() {
  const flags = await fetchFlagsFromBackend();
  return Response.json(flags);
}

export async function POST(request: Request) {
  const body = await request.json();
  await saveFlagToBackend(body);
  return Response.json({ success: true });
}
```

---

## Backend Deep Dive

### Directory Structure

```
backend/
├── api.py              # Main FastAPI entry point
├── core/               # Core business logic
│   ├── agent_service.py
│   ├── threads.py
│   ├── billing/        # Payment logic
│   ├── sandbox/        # Docker container management
│   └── tools/          # AI agent tools
├── pyproject.toml      # Python dependencies (Poetry/uv)
└── supabase/           # Database migrations
    └── migrations/
```

### Understanding FastAPI Structure

#### Main Entry Point

```python
# api.py
from fastapi import FastAPI
from core.api import router as core_router

app = FastAPI()

# Mount routers
app.include_router(core_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

#### Routers (Endpoints)

```python
# core/api.py
from fastapi import APIRouter, Depends
from .agent_service import AgentService

router = APIRouter()

@router.get("/agents")
async def list_agents(
    service: AgentService = Depends()
):
    agents = await service.list_agents()
    return agents

@router.post("/agents")
async def create_agent(
    data: AgentCreate,
    service: AgentService = Depends()
):
    agent = await service.create_agent(data)
    return agent
```

#### Services (Business Logic)

```python
# core/agent_service.py
class AgentService:
    def __init__(self, db: Database):
        self.db = db
    
    async def list_agents(self):
        return await self.db.query("SELECT * FROM agents")
    
    async def create_agent(self, data: AgentCreate):
        return await self.db.insert("agents", data)
```

### Understanding Backend Modules

#### 1. `core/` - Core Business Logic

```
core/
├── agent_service.py    # Agent management
├── threads.py          # Conversation threads
├── auth.py            # Authentication
├── credits.py         # Billing credits
└── run.py             # Agent execution
```

**Pattern**: Each file handles a specific domain

#### 2. `core/tools/` - AI Agent Tools

Tools are **functions the AI can call**:

```python
# core/tools/sb_files_tool.py
from .tool_base import Tool

class FileOperationTool(Tool):
    name = "file_operation"
    description = "Read, write, or modify files"
    
    async def execute(self, operation: str, path: str, content: str = None):
        if operation == "read":
            return read_file(path)
        elif operation == "write":
            return write_file(path, content)
        elif operation == "delete":
            return delete_file(path)
```

The AI decides when to use each tool based on the user's request.

#### 3. `core/sandbox/` - Isolated Execution

Sandboxes are **Docker containers** where agents run code safely:

```python
# core/sandbox/sandbox.py
class Sandbox:
    def __init__(self, sandbox_id: str):
        self.container = docker.create_container(sandbox_id)
    
    async def execute_command(self, command: str):
        result = await self.container.exec(command)
        return result.stdout
    
    async def read_file(self, path: str):
        return await self.container.read_file(path)
```

#### 4. `core/billing/` - Payment Logic

```
billing/
├── api.py                  # Billing endpoints
├── credit_manager.py       # Credit deduction/addition
├── payment_service.py      # Stripe integration
└── subscription_service.py # Subscription management
```

### Understanding Database Migrations

```
supabase/migrations/
├── 20240414161707_basejump-setup.sql
├── 20240524062639_agents_table.sql
└── 20250618000000_credential_profiles.sql
```

**Migration Format**: `YYYYMMDDHHMMSS_description.sql`

**Example Migration**:
```sql
-- 20240524062639_agents_table.sql
CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  system_prompt TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agents_name ON agents(name);
```

**Running Migrations**:
```bash
supabase db push  # Apply pending migrations
```

---

## How to Connect Frontend to Backend

### The Connection Flow

```
Frontend Component
    ↓ (calls)
React Query Hook
    ↓ (uses)
API Client Function
    ↓ (sends HTTP request to)
FastAPI Backend Endpoint
    ↓ (queries)
Supabase Database
```

### Step-by-Step Example

#### 1. Define Backend Endpoint

```python
# backend/core/agent_crud.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = await db.query(
        "SELECT * FROM agents WHERE id = $1",
        agent_id
    )
    return agent
```

Mount in `api.py`:
```python
# backend/api.py
from core.agent_crud import router as agent_router

app.include_router(agent_router, prefix="/api/v1")
# URL: http://localhost:8000/api/v1/agents/{agent_id}
```

#### 2. Create Frontend API Client

```typescript
// frontend/src/lib/api-client.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getAgent(agentId: string) {
  const response = await fetch(`${API_URL}/api/v1/agents/${agentId}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch agent');
  }
  
  return response.json();
}
```

#### 3. Create React Query Hook

```typescript
// frontend/src/hooks/react-query/agents/use-agents.ts
import { useQuery } from '@tanstack/react-query';
import { getAgent } from '@/lib/api-client';

export function useAgent(agentId: string) {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => getAgent(agentId),
    enabled: !!agentId, // Only run if agentId exists
  });
}
```

#### 4. Use in Component

```typescript
// frontend/src/app/agents/[id]/page.tsx
import { useAgent } from '@/hooks/react-query/agents/use-agents';

export default function AgentPage({ params }: { params: { id: string } }) {
  const { data: agent, isLoading, error } = useAgent(params.id);
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading agent</div>;
  
  return (
    <div>
      <h1>{agent.name}</h1>
      <p>{agent.system_prompt}</p>
    </div>
  );
}
```

### Handling Authentication

#### Backend: Verify JWT

```python
# backend/core/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        # Verify Supabase JWT
        user = supabase.auth.get_user(token.credentials)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
```

Use in endpoints:
```python
@router.get("/agents")
async def list_agents(user = Depends(get_current_user)):
    # user is authenticated
    agents = await db.query("SELECT * FROM agents WHERE user_id = $1", user.id)
    return agents
```

#### Frontend: Send JWT

```typescript
// frontend/src/lib/api-client.ts
import { createClient } from '@/lib/supabase/client';

export async function apiFetch(endpoint: string, options?: RequestInit) {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${session?.access_token}`,
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  return response.json();
}
```

### Handling File Uploads

#### Backend: Accept Files

```python
from fastapi import UploadFile, File

@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    # Read file
    content = await file.read()
    
    # Save to storage
    file_url = await storage.upload(file.filename, content)
    
    return {"url": file_url}
```

#### Frontend: Send Files

```typescript
// frontend/src/lib/api-client.ts
export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiFetch('/files/upload', {
    method: 'POST',
    body: formData,
    // Don't set Content-Type - browser will set it with boundary
  });
  
  return response;
}
```

In component:
```typescript
function FileUploader() {
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const result = await uploadFile(file);
    console.log('Uploaded:', result.url);
  };
  
  return <input type="file" onChange={handleUpload} />;
}
```

### Real-Time Updates with Supabase

#### Subscribe to Database Changes

```typescript
// frontend/src/hooks/useProjectRealtime.ts
import { useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';

export function useProjectRealtime(projectId: string) {
  useEffect(() => {
    const supabase = createClient();
    
    const channel = supabase
      .channel(`project:${projectId}`)
      .on(
        'postgres_changes',
        {
          event: '*', // INSERT, UPDATE, DELETE
          schema: 'public',
          table: 'threads',
          filter: `project_id=eq.${projectId}`,
        },
        (payload) => {
          console.log('Change detected:', payload);
          // Invalidate React Query cache to refetch
          queryClient.invalidateQueries(['threads', projectId]);
        }
      )
      .subscribe();
    
    return () => {
      supabase.removeChannel(channel);
    };
  }, [projectId]);
}
```

---

## Mobile App Structure

The mobile app (`apps/mobile/`) follows similar patterns to the frontend but uses React Native:

```
apps/mobile/
├── app/               # Expo Router (similar to Next.js App Router)
│   ├── _layout.tsx   # Root layout
│   └── index.tsx     # Home screen
├── components/       # React Native components
├── hooks/           # Custom hooks
├── api/             # API calls (same as frontend)
├── stores/          # Zustand stores
└── constants/       # Colors, fonts, config
```

### Key Differences from Web

1. **Navigation**: Uses Expo Router (file-based like Next.js)
2. **Styling**: Uses StyleSheet API instead of CSS
3. **Components**: React Native components (`View`, `Text`) instead of HTML

**Example Component**:
```typescript
// components/ChatInput.tsx
import { View, TextInput, TouchableOpacity } from 'react-native';

export function ChatInput({ onSend }: { onSend: (text: string) => void }) {
  const [text, setText] = useState('');
  
  return (
    <View style={styles.container}>
      <TextInput
        value={text}
        onChangeText={setText}
        placeholder="Type a message..."
        style={styles.input}
      />
      <TouchableOpacity onPress={() => onSend(text)}>
        <Text>Send</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    padding: 10,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 8,
    padding: 8,
  },
});
```

---

## SDK and Integration

The Python SDK (`sdk/`) allows developers to programmatically interact with Suna:

```python
# sdk/kortix/agent.py
from kortix import Kortix

# Initialize client
client = Kortix(api_key="your_api_key")

# Create agent
agent = client.agents.create(
    name="My Agent",
    system_prompt="You are a helpful assistant"
)

# Start conversation
thread = client.threads.create(agent_id=agent.id)

# Send message
response = client.threads.send(
    thread_id=thread.id,
    message="Hello!"
)

print(response.content)
```

### SDK Structure

```
sdk/kortix/
├── agent.py        # Agent management
├── thread.py       # Conversation management
├── models.py       # Data models
└── api/            # HTTP client
    ├── agents.py
    └── threads.py
```

---

## Building Production-Ready Features

### Checklist for New Features

1. **Define Requirements**
   - What does the feature do?
   - What data does it need?
   - Who can access it?

2. **Database Schema**
   ```sql
   -- Create migration file
   CREATE TABLE feature_name (
     id UUID PRIMARY KEY,
     user_id UUID REFERENCES auth.users,
     data JSONB,
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **Backend API**
   ```python
   # Create endpoint
   @router.post("/feature")
   async def create_feature(data: FeatureCreate):
       return await service.create_feature(data)
   ```

4. **Frontend API Client**
   ```typescript
   export async function createFeature(data: FeatureCreate) {
     return apiFetch('/api/v1/feature', {
       method: 'POST',
       body: JSON.stringify(data),
     });
   }
   ```

5. **React Query Hook**
   ```typescript
   export function useCreateFeature() {
     return useMutation({
       mutationFn: createFeature,
       onSuccess: () => {
         queryClient.invalidateQueries(['features']);
       },
     });
   }
   ```

6. **UI Component**
   ```typescript
   function FeatureForm() {
     const { mutate, isPending } = useCreateFeature();
     
     const handleSubmit = (data: FeatureCreate) => {
       mutate(data);
     };
     
     return <form onSubmit={handleSubmit}>...</form>;
   }
   ```

7. **Testing**
   - Unit tests for backend logic
   - Integration tests for API endpoints
   - E2E tests for critical user flows

### Best Practices

1. **Separation of Concerns**
   - Components only handle UI
   - Hooks handle data fetching
   - Services handle business logic

2. **Type Safety**
   - Define TypeScript interfaces
   - Share types between frontend/backend

3. **Error Handling**
   ```typescript
   try {
     await apiFetch('/endpoint');
   } catch (error) {
     if (error.status === 401) {
       // Redirect to login
     } else {
       // Show error message
     }
   }
   ```

4. **Loading States**
   ```typescript
   if (isLoading) return <Skeleton />;
   if (error) return <ErrorMessage />;
   return <Data />;
   ```

5. **Caching Strategy**
   ```typescript
   useQuery({
     queryKey: ['data', id],
     queryFn: () => fetchData(id),
     staleTime: 5 * 60 * 1000, // 5 minutes
     gcTime: 30 * 60 * 1000,   // 30 minutes
   });
   ```

---

## Quick Reference

### Finding Things

| What | Where | Example |
|------|-------|---------|
| Pages | `app/*/page.tsx` | `app/agents/page.tsx` |
| UI Components | `components/` | `components/ui/button.tsx` |
| API Calls | `lib/api-client.ts` or `hooks/react-query/` | `hooks/react-query/agents/use-agents.ts` |
| Backend Endpoints | `backend/core/*/api.py` | `backend/core/agent_crud.py` |
| Database Schema | `backend/supabase/migrations/` | `20240524062639_agents_table.sql` |
| Mobile Screens | `apps/mobile/app/` | `apps/mobile/app/index.tsx` |

### Common Commands

```bash
# Frontend development
cd frontend
npm run dev              # Start dev server (http://localhost:3000)

# Backend development
cd backend
uv run api.py           # Start FastAPI server (http://localhost:8000)

# Database migrations
supabase db push        # Apply migrations

# Mobile development
cd apps/mobile
npx expo start          # Start Expo dev server
```

---

## Summary

You now understand:
- ✅ Next.js App Router structure
- ✅ How routing works (file-based)
- ✅ Component organization patterns
- ✅ Hooks, contexts, and providers
- ✅ Backend FastAPI structure
- ✅ Database migrations
- ✅ Connecting frontend to backend
- ✅ Mobile app structure
- ✅ Building production features

**Next Steps:**
1. Pick a feature to implement
2. Start with database schema
3. Build backend endpoint
4. Create frontend hook
5. Build UI component
6. Test end-to-end

Remember: Every feature follows the same pattern: **Database → Backend → API Client → Hook → Component**