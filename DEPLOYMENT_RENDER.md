# Render Deployment Guide for Maqro Dealership Backend

This guide explains how to deploy the Maqro Dealership Backend to Render.

## Prerequisites

- A Render account
- Your code pushed to a Git repository
- Environment variables configured

## Manual Deployment Steps

### 1. Create a New Web Service

1. Go to your Render dashboard
2. Click "New +" and select "Web Service"
3. Connect your Git repository
4. Configure the service with these settings:

### 2. Build Configuration

**Build Command:**
```bash
pip install -r requirements.txt && pip install -e .
```

**Start Command:**
```bash
python app.py
```

### 3. Environment Variables

Set these environment variables in your Render service:

```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
COHERE_API_KEY=your_cohere_api_key (optional)
```

### 4. Package Structure

The project has been updated with proper package structure:

- `setup.py` - Package installation configuration
- `pyproject.toml` - Modern Python packaging configuration
- `src/__init__.py` - Makes src a proper Python package
- `install.sh` - Installation script for Render

### 5. Key Files for Deployment

- `app.py` - Entry point for the application
- `requirements.txt` - Python dependencies
- `setup.py` - Package installation
- `src/maqro_backend/` - Backend application
- `src/maqro_rag/` - RAG functionality

### 6. Testing Deployment

After deployment, you can test the imports by running:

```bash
python test_package_imports.py
```

This will verify that all packages are properly installed and importable.

## Troubleshooting

### "No module named 'maqro_rag'" Error

This error occurs when the packages aren't properly installed. The fixes include:

1. **Proper package structure**: Added `src/__init__.py`
2. **Setup script**: Created `setup.py` for proper installation
3. **Installation script**: Created `install.sh` for Render
4. **Updated pyproject.toml**: Complete package configuration

### Build Failures

If you encounter build failures:

1. Check that all dependencies are in `requirements.txt`
2. Verify the build command includes `pip install -e .`
3. Ensure environment variables are set correctly

### Import Errors

If you get import errors after deployment:

1. Run `python test_package_imports.py` locally to test
2. Check that the `src/` directory is properly structured
3. Verify that `__init__.py` files exist in all package directories

## File Structure

```
Dealerships/
├── app.py                    # Entry point
├── setup.py                  # Package installation
├── requirements.txt          # Dependencies
├── install.sh               # Installation script
├── test_package_imports.py  # Import testing
├── src/
│   ├── __init__.py         # Package marker
│   ├── maqro_backend/      # Backend application
│   └── maqro_rag/          # RAG functionality
└── ...
```

## Environment Setup

Make sure your Render service has:

- **Python 3.8+** runtime
- **Build Command**: `pip install -r requirements.txt && pip install -e .`
- **Start Command**: `python app.py`
- **Environment Variables**: All required API keys and secrets

## Verification

After deployment, your service should:

1. Start without import errors
2. Respond to health checks at `/api/health`
3. Have all RAG functionality available
4. Handle API requests properly

If you encounter any issues, check the Render logs for specific error messages. 