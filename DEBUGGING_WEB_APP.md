# Debugging Guide: Web App Shows Blank Page

## Quick Diagnosis Steps

### 1. Check Browser Console
Open DevTools (F12) → Console tab. Look for:
- **Red errors** (React errors, API errors, etc.)
- **Network errors** (CORS, connection refused, etc.)

### 2. Check Network Tab
DevTools → Network tab → Refresh page:
- Look for `/api/dashboard/stats` and `/api/jobs` requests
- Check if they're:
  - **Pending** (backend not running)
  - **Failed** (CORS error, connection refused)
  - **200 OK** (backend working, but frontend might have React error)

### 3. Check Backend Status
The header now shows a **Backend Status** indicator:
- ✅ **Green "Backend connected"** = Backend is running
- ⚠️ **Red "Backend offline"** = Backend not running

## Common Issues & Fixes

### Issue 1: Blank White Page (Most Common)

**Symptoms:**
- Page loads, shows briefly, then goes blank
- Browser console shows API errors

**Causes:**
1. **Backend not running** (most common)
2. **CORS error** (backend running but CORS misconfigured)
3. **React error** (component crash)

**Fix:**

**Step 1: Start Backend**
```bash
cd backend
source venv/bin/activate  # or: source ../.venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Step 2: Start Frontend** (in another terminal)
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v7.x.x  ready in xxx ms
  ➜  Local:   http://localhost:3000/
```

**Step 3: Open Browser**
Go to `http://localhost:3000`

### Issue 2: CORS Error

**Symptoms:**
- Browser console shows: `Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Fix:**
Check `backend/app/config.py`:
```python
cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
```

Make sure your frontend URL is in this list.

### Issue 3: React Error (Component Crash)

**Symptoms:**
- Browser console shows React error stack trace
- Error Boundary shows error message

**Fix:**
1. Check the error message in the Error Boundary UI
2. Check browser console for full stack trace
3. Common causes:
   - `jobsData?.jobs` is undefined (now handled)
   - Component trying to access property on undefined
   - Missing required props

## Debugging Tools Added

### 1. Error Boundary
- Catches React errors and shows friendly error page
- Prevents entire app from crashing
- Shows error details in collapsible section

### 2. API Request Logging
- All API requests logged to console: `[API] GET /api/dashboard/stats`
- All API errors logged with details
- Check browser console to see what's failing

### 3. Backend Status Indicator
- Shows in header whether backend is reachable
- Updates every 5 seconds
- Helps quickly identify connection issues

### 4. Better Error Messages
- Dashboard shows specific error messages
- Suggests checking if backend is running
- Shows partial data if one API call succeeds

## Step-by-Step Debugging

1. **Open Browser DevTools** (F12)
2. **Go to Console tab** - Look for errors
3. **Go to Network tab** - Check API requests
4. **Check Backend Status** in header
5. **Check Terminal** where backend is running for errors

## Testing Backend Manually

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test dashboard stats
curl http://localhost:8000/api/dashboard/stats

# Test jobs endpoint
curl http://localhost:8000/api/jobs?limit=5
```

If these work but the frontend doesn't, it's a frontend issue (CORS, React error, etc.).

## Still Not Working?

1. **Check both terminals** (backend + frontend) for error messages
2. **Check browser console** for JavaScript errors
3. **Check Network tab** for failed requests
4. **Try hard refresh** (Ctrl+Shift+R or Cmd+Shift+R)
5. **Clear browser cache** and try again

## Expected Behavior

When everything works:
1. Page loads → Shows "Loading..." briefly
2. API calls complete → Shows dashboard with stats cards
3. Stats cards show numbers (even if 0)
4. Jobs table shows (even if empty)
5. No errors in console
6. Backend status shows ✅ green
