# JavaScript Quick Start & Build Guide

## Package Managers Overview

### **npm (Node Package Manager)**
- **What it is**: Default package manager that comes with Node.js
- **Speed**: Moderate
- **Usage**: Most common, widely supported
- **Command prefix**: `npm`

### **npx**
- **What it is**: Package runner that comes with npm (npm 5.2+)
- **Purpose**: Run packages without installing them globally
- **Usage**: Perfect for one-time commands and project initialization
- **Command prefix**: `npx`

### **yarn**
- **What it is**: Alternative package manager by Facebook
- **Speed**: Faster than npm
- **Usage**: Better for monorepos, deterministic installs
- **Command prefix**: `yarn`

### **pnpm**
- **What it is**: Fast, disk space efficient package manager
- **Speed**: Fastest
- **Usage**: Saves disk space by sharing packages across projects
- **Command prefix**: `pnpm`

**Recommendation**: Use **npm** or **npx** for beginners. Use **pnpm** for professional projects (fastest and most efficient).

---

## Quick Start Commands for Popular Frameworks

### **React.js** 
*Most popular UI library for building modern web apps*

```bash
# Using npx (recommended)
npx create-react-app my-app
cd my-app
npm start

# Using Vite (faster, modern alternative)
npm create vite@latest my-app -- --template react
cd my-app
npm install
npm run dev
```

---

### **Next.js** 
*Most popular React framework for production apps with SSR*

```bash
# Using npx (recommended)
npx create-next-app@latest my-app
cd my-app
npm run dev

# With TypeScript
npx create-next-app@latest my-app --typescript
```

---

### **Vue.js**
*Progressive framework, easy to learn*

```bash
# Using npm
npm create vue@latest my-app
cd my-app
npm install
npm run dev

# Quick start without build tools
npm install vue
# Then use Vue via CDN in HTML
```

---

### **Nuxt.js**
*Vue framework with SSR capabilities*

```bash
# Using npx
npx nuxi@latest init my-app
cd my-app
npm install
npm run dev
```

---

### **Angular**
*Full-featured framework for enterprise apps*

```bash
# Install Angular CLI globally
npm install -g @angular/cli

# Create new project
ng new my-app
cd my-app
ng serve
```

---

### **Svelte**
*Compiler-based framework, very fast*

```bash
# Using npm
npm create vite@latest my-app -- --template svelte
cd my-app
npm install
npm run dev
```

---

### **Node.js/Express.js**
*Backend API server*

```bash
# Create project directory
mkdir my-api
cd my-api
npm init -y

# Install Express
npm install express

# Create server.js file and add basic Express code
# Then run:
node server.js
```

---

### **TypeScript Project**
*Add type safety to any JavaScript project*

```bash
# Initialize project
npm init -y

# Install TypeScript
npm install --save-dev typescript

# Initialize TypeScript config
npx tsc --init

# Create index.ts file
# Compile TypeScript
npx tsc

# Run compiled JavaScript
node index.js
```

---

### **React Native**
*Build native mobile apps*

```bash
# Using Expo (easier, recommended for beginners)
npx create-expo-app my-app
cd my-app
npx expo start

# Using React Native CLI (more control)
npx react-native init my-app
cd my-app
npx react-native run-android
# or
npx react-native run-ios
```

---

### **Electron**
*Build desktop apps*

```bash
# Clone quick start
git clone https://github.com/electron/electron-quick-start my-app
cd my-app
npm install
npm start

# Or using Electron Forge
npx create-electron-app my-app
cd my-app
npm start
```

---

## Most Popular Stack for Professional Projects (2025)

### **Frontend Stack**
```bash
# Next.js with TypeScript (most popular choice)
npx create-next-app@latest my-project --typescript --tailwind --app
cd my-project
npm run dev
```

### **Full-Stack Stack**
```bash
# Next.js (handles both frontend and API routes)
npx create-next-app@latest my-fullstack-app --typescript
cd my-fullstack-app
npm run dev

# Or separate: Next.js frontend + Node.js/Express backend
```

### **Why This Stack?**
- **Next.js**: Production-ready, SEO-friendly, has API routes
- **TypeScript**: Type safety, better developer experience
- **Tailwind CSS**: Utility-first styling (usually included)
- **React**: Most popular UI library with huge ecosystem

---

## Building & Compiling Projects

### **React/Next.js/Vue Apps (Web)**

```bash
# Build for production
npm run build

# Output: Creates optimized production files
# - React/Vite: builds to /dist folder
# - Next.js: builds to /.next folder
# - Vue: builds to /dist folder

# Preview production build
npm run preview    # For Vite projects
# or
npm run start      # For Next.js (after build)
```

**What happens during build:**
- JavaScript is minified and optimized
- CSS is extracted and minified
- Images are optimized
- Code is split into chunks for faster loading
- Dead code is removed (tree-shaking)

---

### **TypeScript Projects**

```bash
# Compile TypeScript to JavaScript
npx tsc

# Compile and watch for changes
npx tsc --watch

# Output: Creates .js files from .ts files
# Location: Defined in tsconfig.json (usually /dist or /build)
```

---

### **Node.js Backend/API**

```bash
# No build step needed for plain JavaScript
node server.js

# For TypeScript backend
npm run build      # Compiles TS to JS
npm run start      # Runs compiled JS

# For production deployment
node dist/server.js
```

---

### **React Native (Mobile Apps)**

```bash
# Development build
npm start          # Starts Metro bundler
npx expo start     # For Expo projects

# Production build for Android
cd android
./gradlew assembleRelease
# Output: android/app/build/outputs/apk/release/app-release.apk

# Production build for iOS
npx react-native run-ios --configuration Release
# Output: .ipa file for App Store

# Using Expo (easier)
eas build --platform android
eas build --platform ios
```

---

### **Electron (Desktop Apps)**

```bash
# Development
npm start

# Build for production (all platforms)
npm run make       # Using Electron Forge

# Or using electron-builder
npm run build

# Output: Creates installers for:
# - Windows: .exe installer
# - Mac: .dmg or .app
# - Linux: .AppImage, .deb, or .rpm

# Platform-specific builds
npm run make -- --platform=win32    # Windows only
npm run make -- --platform=darwin   # Mac only
npm run make -- --platform=linux    # Linux only
```

---

## Deployment Quick Reference

### **Web Apps (React/Next.js/Vue)**

**Popular hosting platforms:**
- **Vercel**: Best for Next.js (same company)
  ```bash
  npm install -g vercel
  vercel
  ```

- **Netlify**: Great for static sites and SPAs
  ```bash
  npm run build
  # Drag /dist folder to Netlify
  ```

- **GitHub Pages**: Free for static sites
  ```bash
  npm run build
  npm run deploy    # If configured
  ```

---

### **Backend APIs (Node.js/Express)**

**Popular hosting platforms:**
- **Heroku**: Easy deployment
- **Railway**: Modern, simple
- **DigitalOcean**: Full control
- **AWS/Google Cloud**: Enterprise scale

**Basic deployment:**
```bash
# Most platforms auto-detect and run:
npm install
npm start
```

---

### **Mobile Apps**

**iOS (App Store):**
- Build with Xcode or `eas build`
- Submit through App Store Connect
- Requires Apple Developer account ($99/year)

**Android (Google Play):**
- Build APK/AAB file
- Submit through Google Play Console
- One-time fee ($25)

---

### **Desktop Apps**

**Distribution:**
- Windows: .exe installer or Microsoft Store
- Mac: .dmg installer or Mac App Store
- Linux: .AppImage, .deb, or .rpm package

---

## Common Development Commands

```bash
# Install dependencies
npm install          # or yarn install / pnpm install

# Start development server
npm run dev          # or npm start

# Build for production
npm run build

# Run tests
npm test

# Lint/format code
npm run lint
npm run format

# Update dependencies
npm update

# Check for outdated packages
npm outdated
```

---

## Troubleshooting Tips

### **Port already in use:**
```bash
# Kill process on port 3000 (Linux/Mac)
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### **Node modules issues:**
```bash
# Delete and reinstall
rm -rf node_modules package-lock.json
npm install
```

### **Clear build cache:**
```bash
# Next.js
rm -rf .next

# React/Vite
rm -rf dist

# React Native
npx react-native start --reset-cache
```

---

## Quick Comparison: Which to Use?

| Project Type | Recommended Stack | Quick Start Command |
|--------------|-------------------|---------------------|
| **Simple website** | React + Vite | `npm create vite@latest` |
| **Production web app** | Next.js + TypeScript | `npx create-next-app@latest --typescript` |
| **Learning/small project** | Vue.js | `npm create vue@latest` |
| **Enterprise app** | Angular | `ng new my-app` |
| **Mobile app** | React Native + Expo | `npx create-expo-app` |
| **Desktop app** | Electron | `npx create-electron-app` |
| **Backend API** | Node.js + Express | `npm install express` |
| **Full-stack** | Next.js (frontend + API) | `npx create-next-app@latest` |

---

## Final Notes

- **Always use the latest LTS version of Node.js** (check with `node -v`)
- **Start with npx** - it's the easiest way to initialize projects
- **For professional projects**: Use TypeScript, Next.js, and pnpm
- **Build time**: Small projects (seconds), large projects (1-5 minutes)
- **Most projects follow**: Install → Develop → Build → Deploy