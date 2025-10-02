# Complete Full-Stack Development Guide
## Building Production-Ready Applications with Next.js, TypeScript, and Multiple Backend Options

---

# Table of Contents

1. [Foundation & Setup](#part-1-foundation--setup)
2. [Frontend Development](#part-2-frontend-development)
3. [Backend Development](#part-3-backend-development)
4. [Authentication & Security](#part-4-authentication--security)
5. [Database Integration](#part-5-database-integration)
6. [API Communication](#part-6-api-communication)
7. [State Management](#part-7-state-management)
8. [Deployment & DevOps](#part-8-deployment--devops)
9. [Testing & Debugging](#part-9-testing--debugging)
10. [Advanced Patterns](#part-10-advanced-patterns)

---

# Part 1: Foundation & Setup

## Section 1.1: Understanding the Stack

### Why This Stack?

**Next.js (Frontend)**
- Server-side rendering (SSR) for better SEO
- File-based routing (no manual route configuration)
- Built-in API routes (can serve as backend)
- Image optimization, code splitting out of the box

**TypeScript**
- Type safety catches bugs before runtime
- Better IDE autocomplete and documentation
- Easier refactoring in large codebases

**Backend Options**
- **Node.js/Express:** Same language as frontend, fast I/O
- **Python/FastAPI:** Great for ML/AI, data processing
- **Next.js API Routes:** Simplest for small projects

---

## Section 1.2: Initial Project Setup

### Step 1: Create Next.js Application

```bash
# Using npx (recommended)
npx create-next-app@latest my-fullstack-app --typescript --tailwind --app

# Navigate to project
cd my-fullstack-app

# Install additional dependencies
npm install @tanstack/react-query axios zod
npm install -D @types/node
```

### Step 2: Project Structure Setup

```bash
my-fullstack-app/
├── src/
│   ├── app/                  # Next.js App Router
│   │   ├── layout.tsx        # Root layout
│   │   ├── page.tsx          # Homepage
│   │   ├── api/              # Backend API routes (Option 1)
│   │   ├── auth/             # Auth pages
│   │   └── dashboard/        # Protected pages
│   ├── components/           # React components
│   │   ├── ui/               # Reusable UI (buttons, inputs)
│   │   ├── layout/           # Layout components
│   │   └── features/         # Feature-specific components
│   ├── lib/                  # Utilities
│   │   ├── api.ts            # API client
│   │   ├── auth.ts           # Auth helpers
│   │   └── utils.ts          # General utilities
│   ├── hooks/                # Custom React hooks
│   ├── types/                # TypeScript types
│   └── styles/               # Global styles
├── public/                   # Static assets
├── backend/                  # Separate backend (Option 2)
│   ├── node/                 # Node.js backend
│   └── python/               # Python backend
└── [config files]
```

### Step 3: Environment Setup

Create `.env.local`:

```env
# App Configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Database (we'll add this later)
DATABASE_URL=postgresql://user:password@localhost:5432/mydb

# Authentication (we'll add this later)
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=http://localhost:3000

# API Keys
NEXT_PUBLIC_STRIPE_KEY=pk_test_...
```

---

# Part 2: Frontend Development

## Section 2.1: Building Your First Page

### Understanding Next.js App Router

**File = Route:**
- `app/page.tsx` → `/`
- `app/about/page.tsx` → `/about`
- `app/blog/[slug]/page.tsx` → `/blog/my-post`

### Step 1: Root Layout (app/layout.tsx)

```typescript
import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'My Full Stack App',
  description: 'Built with Next.js and TypeScript',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {/* Global header */}
        <header className="border-b">
          <nav className="container mx-auto px-4 py-4">
            <h1 className="text-2xl font-bold">My App</h1>
          </nav>
        </header>
        
        {/* Page content */}
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
        
        {/* Global footer */}
        <footer className="border-t mt-auto">
          <div className="container mx-auto px-4 py-4 text-center">
            <p>&copy; 2025 My App</p>
          </div>
        </footer>
      </body>
    </html>
  )
}
```

### Step 2: Homepage (app/page.tsx)

```typescript
'use client' // Client component for interactivity

import { useState } from 'react'
import Link from 'next/link'

export default function HomePage() {
  const [count, setCount] = useState(0)
  
  return (
    <div className="space-y-8">
      <h1 className="text-4xl font-bold">Welcome to My App</h1>
      
      {/* Interactive counter */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => setCount(count - 1)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          -
        </button>
        <span className="text-2xl font-bold">{count}</span>
        <button
          onClick={() => setCount(count + 1)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          +
        </button>
      </div>
      
      {/* Navigation */}
      <div className="flex gap-4">
        <Link 
          href="/about"
          className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
        >
          About
        </Link>
        <Link 
          href="/dashboard"
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Dashboard
        </Link>
      </div>
    </div>
  )
}
```

### Step 3: About Page (app/about/page.tsx)

```typescript
import type { Metadata } from 'next'

// SEO metadata (server component)
export const metadata: Metadata = {
  title: 'About - My App',
  description: 'Learn more about our application',
}

// Server component - can fetch data here
export default async function AboutPage() {
  // Simulate data fetching
  const data = await fetch('https://api.example.com/info')
    .then(res => res.json())
    .catch(() => ({ name: 'My App', version: '1.0.0' }))
  
  return (
    <div className="space-y-4">
      <h1 className="text-4xl font-bold">About</h1>
      <p className="text-lg text-gray-600">
        This is a full-stack application built with Next.js, TypeScript, and modern best practices.
      </p>
      <div className="bg-gray-100 p-4 rounded">
        <h2 className="font-semibold">App Info:</h2>
        <p>Name: {data.name}</p>
        <p>Version: {data.version}</p>
      </div>
    </div>
  )
}
```

---

## Section 2.2: Building Reusable Components

### Step 1: Button Component (components/ui/button.tsx)

```typescript
import { ButtonHTMLAttributes, forwardRef } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', className, children, ...props }, ref) => {
    // Base styles
    const baseStyles = 'rounded font-medium transition-colors'
    
    // Variant styles
    const variants = {
      primary: 'bg-blue-500 text-white hover:bg-blue-600',
      secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
      danger: 'bg-red-500 text-white hover:bg-red-600',
    }
    
    // Size styles
    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2',
      lg: 'px-6 py-3 text-lg',
    }
    
    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className || ''}`}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
```

### Step 2: Input Component (components/ui/input.tsx)

```typescript
import { InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div className="space-y-1">
        {label && (
          <label className="block text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`
            w-full px-3 py-2 border rounded
            focus:outline-none focus:ring-2 focus:ring-blue-500
            ${error ? 'border-red-500' : 'border-gray-300'}
            ${className || ''}
          `}
          {...props}
        />
        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
```

### Step 3: Card Component (components/ui/card.tsx)

```typescript
import { HTMLAttributes } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: string
  description?: string
}

export function Card({ title, description, children, className, ...props }: CardProps) {
  return (
    <div
      className={`bg-white rounded-lg shadow-md p-6 ${className || ''}`}
      {...props}
    >
      {title && (
        <h3 className="text-xl font-semibold mb-2">{title}</h3>
      )}
      {description && (
        <p className="text-gray-600 mb-4">{description}</p>
      )}
      {children}
    </div>
  )
}
```

---

## Section 2.3: Forms and Validation

### Step 1: Define Form Schema (types/auth.ts)

```typescript
import { z } from 'zod'

// Login form schema
export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

export type LoginFormData = z.infer<typeof loginSchema>

// Registration form schema
export const registerSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
})

export type RegisterFormData = z.infer<typeof registerSchema>
```

### Step 2: Login Form Component (components/auth/login-form.tsx)

```typescript
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { loginSchema, type LoginFormData } from '@/types/auth'

export function LoginForm() {
  const router = useRouter()
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  })
  const [errors, setErrors] = useState<Partial<LoginFormData>>({})
  const [isLoading, setIsLoading] = useState(false)
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})
    
    // Validate with Zod
    const result = loginSchema.safeParse(formData)
    
    if (!result.success) {
      // Extract errors from Zod
      const fieldErrors: Partial<LoginFormData> = {}
      result.error.errors.forEach((err) => {
        if (err.path[0]) {
          fieldErrors[err.path[0] as keyof LoginFormData] = err.message
        }
      })
      setErrors(fieldErrors)
      return
    }
    
    // Submit to API
    setIsLoading(true)
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result.data),
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Login failed')
      }
      
      const data = await response.json()
      
      // Store token (we'll improve this later)
      localStorage.setItem('token', data.token)
      
      // Redirect to dashboard
      router.push('/dashboard')
    } catch (error) {
      setErrors({
        email: error instanceof Error ? error.message : 'Login failed',
      })
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Email"
        type="email"
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        error={errors.email}
        disabled={isLoading}
      />
      
      <Input
        label="Password"
        type="password"
        value={formData.password}
        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
        error={errors.password}
        disabled={isLoading}
      />
      
      <Button
        type="submit"
        variant="primary"
        className="w-full"
        disabled={isLoading}
      >
        {isLoading ? 'Logging in...' : 'Log In'}
      </Button>
    </form>
  )
}
```

---

# Part 3: Backend Development

## Section 3.1: Option 1 - Next.js API Routes

### Step 1: Create API Route (app/api/auth/login/route.ts)

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'

// Validation schema
const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

// Mock database (replace with real database)
const users = [
  {
    id: '1',
    email: 'user@example.com',
    password: await bcrypt.hash('password123', 10), // Hashed password
    name: 'John Doe',
  },
]

export async function POST(request: NextRequest) {
  try {
    // Parse and validate request body
    const body = await request.json()
    const result = loginSchema.safeParse(body)
    
    if (!result.success) {
      return NextResponse.json(
        { message: 'Invalid input', errors: result.error.errors },
        { status: 400 }
      )
    }
    
    const { email, password } = result.data
    
    // Find user
    const user = users.find(u => u.email === email)
    if (!user) {
      return NextResponse.json(
        { message: 'Invalid credentials' },
        { status: 401 }
      )
    }
    
    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.password)
    if (!isValidPassword) {
      return NextResponse.json(
        { message: 'Invalid credentials' },
        { status: 401 }
      )
    }
    
    // Generate JWT token
    const token = jwt.sign(
      { userId: user.id, email: user.email },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    )
    
    // Return success response
    return NextResponse.json({
      message: 'Login successful',
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
      },
    })
    
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { message: 'Internal server error' },
      { status: 500 }
    )
  }
}
```

### Step 2: Protected API Route (app/api/users/profile/route.ts)

```typescript
import { NextRequest, NextResponse } from 'next/server'
import jwt from 'jsonwebtoken'

// Middleware to verify JWT
function verifyToken(request: NextRequest) {
  const authHeader = request.headers.get('authorization')
  
  if (!authHeader?.startsWith('Bearer ')) {
    return null
  }
  
  const token = authHeader.substring(7)
  
  try {
    const decoded = jwt.verify(
      token,
      process.env.JWT_SECRET || 'your-secret-key'
    ) as { userId: string; email: string }
    return decoded
  } catch {
    return null
  }
}

export async function GET(request: NextRequest) {
  // Verify authentication
  const user = verifyToken(request)
  
  if (!user) {
    return NextResponse.json(
      { message: 'Unauthorized' },
      { status: 401 }
    )
  }
  
  // Fetch user profile (mock data)
  const profile = {
    id: user.userId,
    email: user.email,
    name: 'John Doe',
    createdAt: '2025-01-01',
  }
  
  return NextResponse.json(profile)
}

export async function PUT(request: NextRequest) {
  const user = verifyToken(request)
  
  if (!user) {
    return NextResponse.json(
      { message: 'Unauthorized' },
      { status: 401 }
    )
  }
  
  const body = await request.json()
  
  // Update user profile logic here
  // ...
  
  return NextResponse.json({
    message: 'Profile updated successfully',
  })
}
```

---

## Section 3.2: Option 2 - Separate Node.js/Express Backend

### Step 1: Setup Express Server (backend/node/server.ts)

```bash
# In project root
mkdir -p backend/node
cd backend/node

# Initialize package.json
npm init -y

# Install dependencies
npm install express cors dotenv bcryptjs jsonwebtoken
npm install -D typescript @types/express @types/node ts-node nodemon

# Initialize TypeScript
npx tsc --init
```

**backend/node/server.ts:**

```typescript
import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import authRoutes from './routes/auth'
import userRoutes from './routes/users'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 8000

// Middleware
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
}))
app.use(express.json())

// Routes
app.use('/api/auth', authRoutes)
app.use('/api/users', userRoutes)

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// Error handling middleware
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err)
  res.status(500).json({
    message: 'Internal server error',
    error: process.env.NODE_ENV === 'development' ? err.message : undefined,
  })
})

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`)
})
```

### Step 2: Auth Routes (backend/node/routes/auth.ts)

```typescript
import { Router } from 'express'
import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'
import { z } from 'zod'

const router = Router()

// Mock database
const users: any[] = []

// Validation schemas
const registerSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8),
})

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
})

// Register endpoint
router.post('/register', async (req, res) => {
  try {
    const result = registerSchema.safeParse(req.body)
    
    if (!result.success) {
      return res.status(400).json({
        message: 'Validation failed',
        errors: result.error.errors,
      })
    }
    
    const { name, email, password } = result.data
    
    // Check if user exists
    if (users.find(u => u.email === email)) {
      return res.status(400).json({ message: 'User already exists' })
    }
    
    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10)
    
    // Create user
    const user = {
      id: Date.now().toString(),
      name,
      email,
      password: hashedPassword,
      createdAt: new Date().toISOString(),
    }
    
    users.push(user)
    
    // Generate token
    const token = jwt.sign(
      { userId: user.id, email: user.email },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    )
    
    res.status(201).json({
      message: 'User created successfully',
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
      },
    })
  } catch (error) {
    res.status(500).json({ message: 'Server error' })
  }
})

// Login endpoint
router.post('/login', async (req, res) => {
  try {
    const result = loginSchema.safeParse(req.body)
    
    if (!result.success) {
      return res.status(400).json({
        message: 'Validation failed',
        errors: result.error.errors,
      })
    }
    
    const { email, password } = result.data
    
    // Find user
    const user = users.find(u => u.email === email)
    if (!user) {
      return res.status(401).json({ message: 'Invalid credentials' })
    }
    
    // Verify password
    const isValid = await bcrypt.compare(password, user.password)
    if (!isValid) {
      return res.status(401).json({ message: 'Invalid credentials' })
    }
    
    // Generate token
    const token = jwt.sign(
      { userId: user.id, email: user.email },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '7d' }
    )
    
    res.json({
      message: 'Login successful',
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
      },
    })
  } catch (error) {
    res.status(500).json({ message: 'Server error' })
  }
})

export default router
```

### Step 3: Authentication Middleware (backend/node/middleware/auth.ts)

```typescript
import { Request, Response, NextFunction } from 'express'
import jwt from 'jsonwebtoken'

export interface AuthRequest extends Request {
  user?: {
    userId: string
    email: string
  }
}

export function authenticate(
  req: AuthRequest,
  res: Response,
  next: NextFunction
) {
  const authHeader = req.headers.authorization
  
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ message: 'No token provided' })
  }
  
  const token = authHeader.substring(7)
  
  try {
    const decoded = jwt.verify(
      token,
      process.env.JWT_SECRET || 'your-secret-key'
    ) as { userId: string; email: string }
    
    req.user = decoded
    next()
  } catch (error) {
    return res.status(401).json({ message: 'Invalid token' })
  }
}
```

---

## Section 3.3: Option 3 - Python/FastAPI Backend

### Step 1: Setup FastAPI (backend/python/main.py)

```bash
# In project root
mkdir -p backend/python
cd backend/python

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] python-multipart pydantic[email]

# Create requirements.txt
pip freeze > requirements.txt
```

**backend/python/main.py:**

```python
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Mock database
users_db = []

# Pydantic models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    name: str
    email: str
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Helper functions
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Routes
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    # Check if user exists
    if any(u["email"] == user_data.email for u in users_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Hash password
    hashed_password = pwd_context.hash(user_data.password)
    
    # Create user
    user = {
        "id": str(len(users_db) + 1),
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_password,
        "created_at": datetime.utcnow().isoformat()
    }
    
    users_db.append(user)
    
    # Create token
    token = create_access_token({"user_id": user["id"], "email": user["email"]})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": User(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            created_at=user["created_at"]
        )
    }

@app.post("/api/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    # Find user
    user = next((u for u in users_db if u["email"] == credentials.email), None)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not pwd_context.verify(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_