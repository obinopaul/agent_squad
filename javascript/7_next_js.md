# Complete Next.js Framework Guide

## Table of Contents
1. [Introduction to Next.js](#introduction)
2. [Installation & Project Setup](#installation)
3. [Project Structure](#project-structure)
4. [Routing System](#routing-system)
5. [Layouts & Pages](#layouts-and-pages)
6. [Navigation & Linking](#navigation-and-linking)
7. [Server & Client Components](#server-and-client-components)
8. [Data Fetching](#data-fetching)
9. [Data Mutations](#data-mutations)
10. [Caching & Revalidation](#caching-and-revalidation)
11. [Error Handling](#error-handling)
12. [Styling with CSS](#styling-with-css)
13. [Image Optimization](#image-optimization)
14. [Font Optimization](#font-optimization)
15. [Metadata & SEO](#metadata-and-seo)
16. [Route Handlers](#route-handlers)
17. [Middleware](#middleware)
18. [Deployment](#deployment)
19. [Configuration](#configuration)
20. [CLI Commands](#cli-commands)
21. [Edge Runtime](#edge-runtime)
22. [Directives](#directives)
23. [Built-in Functions](#built-in-functions)
24. [Project Organization](#project-organization)

---

## Introduction to Next.js {#introduction}

Next.js is a React framework developed by Vercel that provides a complete solution for building modern web applications. While React focuses on building user interfaces, Next.js adds:

- **File-based routing**: Pages are automatically created from file structure
- **Server-side rendering (SSR)**: Render React on the server for better performance
- **Static site generation (SSG)**: Pre-render pages at build time
- **API routes**: Build backend endpoints within your app
- **Automatic code splitting**: Only load the JavaScript needed for each page
- **Built-in optimization**: Images, fonts, and scripts are optimized automatically
- **TypeScript support**: First-class TypeScript integration

**Key Concept**: Next.js uses the App Router (introduced in v13+), which leverages React Server Components by default. This is a fundamental shift from the older Pages Router.

---

## Installation & Project Setup {#installation}

### Creating a New Next.js Project

```bash
# Using npx (recommended)
npx create-next-app@latest my-app

# Using yarn
yarn create next-app my-app

# Using pnpm
pnpm create next-app my-app
```

### Installation Prompts

When you run `create-next-app`, you'll be asked:

```
Would you like to use TypeScript? Yes/No
Would you like to use ESLint? Yes/No
Would you like to use Tailwind CSS? Yes/No
Would you like to use `src/` directory? Yes/No
Would you like to use App Router? Yes/No (recommended)
Would you like to customize the default import alias? Yes/No
```

**Recommended Setup**:
- TypeScript: Yes (for type safety)
- ESLint: Yes (for code quality)
- Tailwind CSS: Yes (for rapid styling)
- src/ directory: Optional (for cleaner organization)
- App Router: Yes (modern approach)
- Import alias: No (unless you prefer custom paths)

### Starting the Development Server

```bash
cd my-app
npm run dev
# or
yarn dev
# or
pnpm dev
```

Your app will be available at `http://localhost:3000`

---

## Project Structure {#project-structure}

### Default File Structure

```
my-app/
├── app/                    # App Router directory (main application code)
│   ├── layout.tsx         # Root layout (wraps all pages)
│   ├── page.tsx           # Home page (/)
│   ├── globals.css        # Global styles
│   └── favicon.ico        # Favicon
├── public/                # Static assets (served as-is)
│   ├── images/
│   └── fonts/
├── node_modules/          # Dependencies
├── package.json           # Project dependencies and scripts
├── tsconfig.json          # TypeScript configuration
├── next.config.js         # Next.js configuration
├── .eslintrc.json        # ESLint configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── .gitignore            # Git ignore rules
```

### Understanding Top-Level Folders

- **`app/`**: Contains all your application code using the App Router
- **`public/`**: Static files accessible from the root URL (e.g., `/images/logo.png`)
- **`components/`** (optional): Reusable React components
- **`lib/`** (optional): Utility functions and helpers
- **`types/`** (optional): TypeScript type definitions

### Top-Level Files

- **`next.config.js`**: Next.js configuration
- **`package.json`**: Project dependencies and scripts
- **`tsconfig.json`**: TypeScript compiler options
- **`.env.local`**: Environment variables (not committed to git)
- **`middleware.ts`**: Middleware for request interception

---

## Routing System {#routing-system}

Next.js uses **file-system based routing**. The file structure in the `app/` directory determines your routes.

### Routing Conventions

| File | Purpose | Route |
|------|---------|-------|
| `page.tsx` | Defines a unique page/route | Required to make route accessible |
| `layout.tsx` | Shared UI wrapper for pages | Wraps pages in that folder |
| `loading.tsx` | Loading UI (Suspense boundary) | Shows while page loads |
| `error.tsx` | Error UI boundary | Shows when errors occur |
| `not-found.tsx` | 404 UI | Shows for unmatched routes |
| `route.ts` | API endpoint | Server-side API route |

### Basic Routes

```
app/
├── page.tsx              → /
├── about/
│   └── page.tsx         → /about
├── blog/
│   └── page.tsx         → /blog
└── contact/
    └── page.tsx         → /contact
```

**Example: Creating an About Page**

```tsx
// app/about/page.tsx
export default function AboutPage() {
  return (
    <div>
      <h1>About Us</h1>
      <p>Welcome to our about page!</p>
    </div>
  );
}
```

### Nested Routes

Create nested routes by nesting folders:

```
app/
└── blog/
    ├── page.tsx         → /blog
    └── [slug]/
        └── page.tsx     → /blog/my-post
```

```tsx
// app/blog/page.tsx
export default function BlogPage() {
  return <h1>Blog Home</h1>;
}

// app/blog/[slug]/page.tsx
export default function BlogPost({ params }: { params: { slug: string } }) {
  return <h1>Post: {params.slug}</h1>;
}
```

### Dynamic Routes

Use square brackets `[param]` for dynamic segments:

```
app/
└── products/
    └── [id]/
        └── page.tsx     → /products/1, /products/2, etc.
```

```tsx
// app/products/[id]/page.tsx
export default function ProductPage({ params }: { params: { id: string } }) {
  return (
    <div>
      <h1>Product ID: {params.id}</h1>
    </div>
  );
}
```

### Catch-All Routes

Use `[...slug]` to match all subsequent segments:

```
app/
└── docs/
    └── [...slug]/
        └── page.tsx     → /docs/a, /docs/a/b, /docs/a/b/c
```

```tsx
// app/docs/[...slug]/page.tsx
export default function DocsPage({ params }: { params: { slug: string[] } }) {
  return (
    <div>
      <h1>Docs</h1>
      <p>Path: {params.slug.join('/')}</p>
    </div>
  );
}
```

### Optional Catch-All Routes

Use `[[...slug]]` to make the catch-all optional (matches parent route too):

```
app/
└── shop/
    └── [[...category]]/
        └── page.tsx     → /shop, /shop/clothing, /shop/clothing/mens
```

### Route Groups

Use parentheses `(folder)` to organize routes without affecting the URL:

```
app/
├── (marketing)/
│   ├── about/
│   │   └── page.tsx     → /about
│   └── contact/
│       └── page.tsx     → /contact
└── (shop)/
    ├── products/
    │   └── page.tsx     → /products
    └── cart/
        └── page.tsx     → /cart
```

**Purpose**: Group related routes and apply different layouts without changing URLs.

```tsx
// app/(marketing)/layout.tsx
export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <nav>Marketing Nav</nav>
      {children}
    </div>
  );
}
```

### Private Folders

Use underscore prefix `_folder` to create private folders (excluded from routing):

```
app/
├── _components/         # Not a route
│   └── Header.tsx
├── _lib/               # Not a route
│   └── utils.ts
└── page.tsx            → /
```

### Parallel Routes

Use `@folder` to render multiple pages in the same layout simultaneously:

```
app/
├── @team/
│   └── page.tsx
├── @analytics/
│   └── page.tsx
└── layout.tsx
```

```tsx
// app/layout.tsx
export default function Layout({
  children,
  team,
  analytics,
}: {
  children: React.ReactNode;
  team: React.ReactNode;
  analytics: React.ReactNode;
}) {
  return (
    <div>
      {children}
      <div className="grid grid-cols-2">
        {team}
        {analytics}
      </div>
    </div>
  );
}
```

### Intercepting Routes

Use `(.)folder` to intercept routes and show them in a modal:

```
app/
├── photos/
│   ├── [id]/
│   │   └── page.tsx     → /photos/1
│   └── (.)photos/
│       └── [id]/
│           └── page.tsx  # Shows in modal when navigating from same level
```

**Intercepting Conventions**:
- `(.)` - same level
- `(..)` - one level up
- `(..)(..)` - two levels up
- `(...)` - from root

---

## Layouts & Pages {#layouts-and-pages}

### Root Layout (Required)

Every Next.js app must have a root layout in `app/layout.tsx`:

```tsx
// app/layout.tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header>Site Header</header>
        <main>{children}</main>
        <footer>Site Footer</footer>
      </body>
    </html>
  );
}
```

**Key Points**:
- Must include `<html>` and `<body>` tags
- Only the root layout can modify `<html>` and `<body>`
- Shared across all pages in your app
- Can fetch data (it's a Server Component by default)

### Nested Layouts

Create layouts for specific sections:

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      <aside>Dashboard Sidebar</aside>
      <section>{children}</section>
    </div>
  );
}

// app/dashboard/page.tsx
export default function DashboardPage() {
  return <h1>Dashboard Home</h1>;
}
```

**Layout Hierarchy**: Root Layout → Dashboard Layout → Page

### Pages

Pages are the UI for a specific route:

```tsx
// app/page.tsx (homepage)
export default function Home() {
  return <h1>Welcome Home</h1>;
}

// app/about/page.tsx
export default function About() {
  return <h1>About Us</h1>;
}
```

### Templates

Templates are similar to layouts but create new instances on navigation (layouts preserve state):

```tsx
// app/template.tsx
export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="template-wrapper">{children}</div>;
}
```

**Use Cases**:
- When you need to reset state on navigation
- When you want animations on route changes
- When you need fresh component instances

---

## Navigation & Linking {#navigation-and-linking}

### Using the Link Component

The `Link` component enables client-side navigation:

```tsx
import Link from 'next/link';

export default function Nav() {
  return (
    <nav>
      <Link href="/">Home</Link>
      <Link href="/about">About</Link>
      <Link href="/blog/my-post">Blog Post</Link>
    </nav>
  );
}
```

### Dynamic Links

```tsx
const posts = [
  { id: 1, title: 'First Post' },
  { id: 2, title: 'Second Post' },
];

export default function BlogList() {
  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>
          <Link href={`/blog/${post.id}`}>{post.title}</Link>
        </li>
      ))}
    </ul>
  );
}
```

### Link Props

```tsx
<Link
  href="/about"
  prefetch={true}          // Prefetch in background (default: true)
  replace={false}          // Replace history instead of push
  scroll={true}            // Scroll to top after navigation
  shallow={false}          // Update URL without rerunning data fetching
>
  About
</Link>
```

### Programmatic Navigation

Use the `useRouter` hook (client component only):

```tsx
'use client';

import { useRouter } from 'next/navigation';

export default function LoginButton() {
  const router = useRouter();

  const handleLogin = async () => {
    // Perform login logic
    router.push('/dashboard');
  };

  return <button onClick={handleLogin}>Login</button>;
}
```

**Router Methods**:
- `router.push('/path')` - Navigate to new route (adds to history)
- `router.replace('/path')` - Navigate without adding to history
- `router.refresh()` - Refresh current route
- `router.back()` - Go back
- `router.forward()` - Go forward
- `router.prefetch('/path')` - Manually prefetch a route

### usePathname Hook

Get the current pathname:

```tsx
'use client';

import { usePathname } from 'next/navigation';

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav>
      <Link href="/" className={pathname === '/' ? 'active' : ''}>
        Home
      </Link>
      <Link href="/about" className={pathname === '/about' ? 'active' : ''}>
        About
      </Link>
    </nav>
  );
}
```

### useSearchParams Hook

Access URL search parameters:

```tsx
'use client';

import { useSearchParams } from 'next/navigation';

export default function Search() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q');

  return <div>Search query: {query}</div>;
}
```

---

## Server & Client Components {#server-and-client-components}

This is one of the most important concepts in Next.js 13+.

### Server Components (Default)

By default, all components in the `app/` directory are **Server Components**:

```tsx
// app/page.tsx (Server Component by default)
export default async function Page() {
  // This runs on the server only
  const data = await fetch('https://api.example.com/data');
  const json = await data.json();

  return (
    <div>
      <h1>Server Component</h1>
      <pre>{JSON.stringify(json, null, 2)}</pre>
    </div>
  );
}
```

**Benefits**:
- Direct database/API access (no CORS issues)
- Keep sensitive data on server (API keys, tokens)
- Reduce JavaScript bundle size
- Automatic code splitting
- Better SEO (fully rendered HTML)

**Limitations**:
- Cannot use React hooks (useState, useEffect, etc.)
- Cannot use browser APIs
- Cannot add event listeners (onClick, onChange, etc.)

### Client Components

Use the `'use client'` directive at the top of the file:

```tsx
'use client';

import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
```

**When to Use Client Components**:
- Need React hooks (useState, useEffect, useContext, etc.)
- Need event listeners (onClick, onChange, etc.)
- Need browser-only APIs (localStorage, window, etc.)
- Need third-party libraries that use hooks

### Composition Pattern

Combine Server and Client Components effectively:

```tsx
// app/page.tsx (Server Component)
import ClientCounter from '@/components/ClientCounter';

export default async function Page() {
  // Fetch data on server
  const data = await fetch('https://api.example.com/data');
  const json = await data.json();

  return (
    <div>
      <h1>Server Data: {json.title}</h1>
      {/* Pass server data to client component */}
      <ClientCounter initialCount={json.count} />
    </div>
  );
}
```

```tsx
// components/ClientCounter.tsx (Client Component)
'use client';

import { useState } from 'react';

export default function ClientCounter({ initialCount }: { initialCount: number }) {
  const [count, setCount] = useState(initialCount);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
```

### Server-Only Code

Ensure code only runs on server:

```tsx
// lib/server-only-utils.ts
import 'server-only';

export async function getSecretData() {
  const secret = process.env.SECRET_API_KEY;
  // This will error if imported in a client component
  return fetch(`https://api.example.com/secret?key=${secret}`);
}
```

### Client-Only Code

Ensure code only runs on client:

```tsx
// lib/client-only-utils.ts
import 'client-only';

export function useLocalStorage(key: string) {
  // This will error if imported in a server component
  return localStorage.getItem(key);
}
```

---

## Data Fetching {#data-fetching}

Next.js extends the native `fetch()` API with caching and revalidation.

### Fetching in Server Components

```tsx
// app/posts/page.tsx
async function getPosts() {
  const res = await fetch('https://jsonplaceholder.typicode.com/posts');
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

export default async function PostsPage() {
  const posts = await getPosts();

  return (
    <ul>
      {posts.map((post: any) => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}
```

### Parallel Data Fetching

Fetch multiple resources simultaneously:

```tsx
async function getUser(id: string) {
  const res = await fetch(`https://api.example.com/users/${id}`);
  return res.json();
}

async function getPosts(userId: string) {
  const res = await fetch(`https://api.example.com/posts?userId=${userId}`);
  return res.json();
}

export default async function UserProfile({ params }: { params: { id: string } }) {
  // Fetch in parallel
  const [user, posts] = await Promise.all([
    getUser(params.id),
    getPosts(params.id),
  ]);

  return (
    <div>
      <h1>{user.name}</h1>
      <ul>
        {posts.map((post: any) => (
          <li key={post.id}>{post.title}</li>
        ))}
      </ul>
    </div>
  );
}
```

### Sequential Data Fetching

When one fetch depends on another:

```tsx
export default async function Page() {
  // First fetch
  const user = await fetch('https://api.example.com/user/1').then(r => r.json());
  
  // Second fetch depends on first
  const posts = await fetch(`https://api.example.com/posts?userId=${user.id}`).then(r => r.json());

  return <div>{/* render user and posts */}</div>;
}
```

### Fetching with TypeScript

```tsx
interface Post {
  id: number;
  title: string;
  body: string;
}

async function getPosts(): Promise<Post[]> {
  const res = await fetch('https://jsonplaceholder.typicode.com/posts');
  if (!res.ok) throw new Error('Failed to fetch posts');
  return res.json();
}

export default async function PostsPage() {
  const posts = await getPosts();

  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}
```

### Streaming with Suspense

Show loading states while data fetches:

```tsx
// app/posts/page.tsx
import { Suspense } from 'react';

async function Posts() {
  const res = await fetch('https://api.example.com/posts');
  const posts = await res.json();

  return (
    <ul>
      {posts.map((post: any) => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  );
}

export default function Page() {
  return (
    <div>
      <h1>Posts</h1>
      <Suspense fallback={<div>Loading posts...</div>}>
        <Posts />
      </Suspense>
    </div>
  );
}
```

### Loading UI

Create automatic loading states with `loading.tsx`:

```tsx
// app/posts/loading.tsx
export default function Loading() {
  return <div>Loading posts...</div>;
}

// app/posts/page.tsx
export default async function PostsPage() {
  const posts = await fetch('https://api.example.com/posts').then(r => r.json());
  return <ul>{/* render posts */}</ul>;
}
```

---

## Data Mutations {#data-mutations}

### Server Actions

Server Actions allow you to run server-side code directly from your components:

```tsx
// app/actions.ts
'use server';

export async function createPost(formData: FormData) {
  const title = formData.get('title');
  const body = formData.get('body');

  const res = await fetch('https://api.example.com/posts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, body }),
  });

  return res.json();
}
```

```tsx
// app/create-post/page.tsx
import { createPost } from '../actions';

export default function CreatePostPage() {
  return (
    <form action={createPost}>
      <input type="text" name="title" placeholder="Title" required />
      <textarea name="body" placeholder="Body" required />
      <button type="submit">Create Post</button>
    </form>
  );
}
```

### Server Actions with useFormState

Add loading states and error handling:

```tsx
'use client';

import { useFormState, useFormStatus } from 'react-dom';
import { createPost } from '../actions';

function SubmitButton() {
  const { pending } = useFormStatus();
  
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Creating...' : 'Create Post'}
    </button>
  );
}

export default function CreatePostForm() {
  const [state, formAction] = useFormState(createPost, { message: '' });

  return (
    <form action={formAction}>
      <input type="text" name="title" placeholder="Title" required />
      <textarea name="body" placeholder="Body" required />
      <SubmitButton />
      {state?.message && <p>{state.message}</p>}
    </form>
  );
}
```

### Revalidating After Mutations

Use `revalidatePath` or `revalidateTag` to update cached data:

```tsx
'use server';

import { revalidatePath } from 'next/cache';

export async function createPost(formData: FormData) {
  const res = await fetch('https://api.example.com/posts', {
    method: 'POST',
    body: JSON.stringify({
      title: formData.get('title'),
      body: formData.get('body'),
    }),
  });

  // Revalidate the posts page to show new post
  revalidatePath('/posts');

  return { message: 'Post created successfully' };
}
```

### Optimistic Updates

Update UI immediately before server confirms:

```tsx
'use client';

import { useOptimistic } from 'react';
import { likePost } from '../actions';

export default function Post({ post }: { post: any }) {
  const [optimisticLikes, addOptimisticLike] = useOptimistic(
    post.likes,
    (state, newLike) => state + 1
  );

  const handleLike = async () => {
    addOptimisticLike(1);
    await likePost(post.id);
  };

  return (
    <div>
      <h2>{post.title}</h2>
      <p>Likes: {optimisticLikes}</p>
      <button onClick={handleLike}>Like</button>
    </div>
  );
}
```

---

## Caching & Revalidation {#caching-and-revalidation}

Next.js has multiple layers of caching.

### Request Memoization

Automatically deduplicates identical fetch requests:

```tsx
async function getUser(id: string) {
  const res = await fetch(`https://api.example.com/users/${id}`);
  return res.json();
}

export default async function Page() {
  // Both calls use the same cached data
  const user1 = await getUser('1');
  const user2 = await getUser('1');  // Not fetched again!

  return <div>{user1.name}</div>;
}
```

### Data Cache

Cache fetch requests across deploys:

```tsx
// Cached indefinitely (default)
fetch('https://api.example.com/data');

// Revalidate every 60 seconds
fetch('https://api.example.com/data', { next: { revalidate: 60 } });

// Never cache (opt out)
fetch('https://api.example.com/data', { cache: 'no-store' });
```

### Full Route Cache

Static routes are cached at build time:

```tsx
// Statically generated at build time
export default async function Page() {
  const data = await fetch('https://api.example.com/data');
  return <div>{/* render */}</div>;
}
```

### Router Cache

Client-side cache for visited routes:

```tsx
// When you navigate with Link, the route is cached
<Link href="/about">About</Link>
```

### Revalidation Strategies

**Time-based Revalidation**:

```tsx
// Revalidate every 60 seconds
fetch('https://api.example.com/data', { next: { revalidate: 60 } });

// Or at the page level
export const revalidate = 60;

export default async function Page() {
  const data = await fetch('https://api.example.com/data');
  return <div>{/* render */}</div>;
}
```

**On-demand Revalidation**:

```tsx
'use server';

import { revalidatePath, revalidateTag } from 'next/cache';

export async function updatePost() {
  // Revalidate specific path
  revalidatePath('/posts');
  
  // Or revalidate by tag
  revalidateTag('posts');
}

// Using tags in fetch
fetch('https://api.example.com/posts', {
  next: { tags: ['posts'] }
});
```

### Dynamic Rendering

Force dynamic rendering (no caching):

```tsx
export const dynamic = 'force-dynamic';

export default async function Page() {
  // Always fetches fresh data
  const data = await fetch('https://api.example.com/data');
  return <div>{/* render */}</div>;
}
```

### Segment Config Options

Configure caching per route:

```tsx
// app/posts/page.tsx
export const dynamic = 'auto'; // Default: cache when possible
// 'auto' | 'force-dynamic' | 'error' | 'force-static'

export const revalidate = 3600; // Revalidate every hour

export const fetchCache = 'auto'; // Default fetch cache behavior
// 'auto' | 'default-cache' | 'only-cache' | 'force-cache' | 'force-no-store' | 'default-no-store' | 'only-no-store'

export default async function Page() {
  // ...
}
```

---

## Error Handling {#error-handling}

### Error Boundaries

Create `error.tsx` to handle errors in a route segment:

```tsx
// app/posts/error.tsx
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <p>{error.message}</p>
      <button onClick={() => reset()}>Try again</button>
    </div>
  );
}
```

### Global Error Handling

Create `global-error.tsx` in the root for global errors:

```tsx
// app/global-error.tsx
'use client';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <h2>Something went wrong globally!</h2>
        <button onClick={() => reset()}>Try again</button>
      </body>
    </html>
  );
}
```

### Not Found Pages

Create `not-found.tsx` for 404 errors:

```tsx
// app/not-found.tsx
import Link from 'next/link';

export default function NotFound() {
  return (
    <div>
      <h2>Not Found</h2>
      <p>Could not find requested resource</p>
      <Link href="/">Return Home</Link>
    </div>
  );
}
```

Trigger programmatically:

```tsx
import { notFound } from 'next/navigation';

async function getPost(id: string) {
  const res = await fetch(`https://api.example.com/posts/${id}`);
  if (!res.ok) notFound();
  return