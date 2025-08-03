# Deploying Maqro Backend to Render

This guide will help you deploy your Maqro backend to Render.

## Prerequisites

1. A Render account (free tier available)
2. Your project pushed to a Git repository (GitHub, GitLab, etc.)
3. Supabase database setup
4. OpenAI API key

## Step 1: Prepare Your Repository

Make sure your repository contains:
- `requirements.txt` (already exists)
- `render.yaml` (created for deployment)
- `start.sh` (created for deployment)
- `build.sh` (created for deployment)

## Step 2: Set Up Environment Variables in Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Create a new Web Service
3. Connect your Git repository
4. Configure the following environment variables:

### Required Environment Variables:

**Database Configuration:**
- `SUPABASE_DB_URL` - Your Supabase database URL
- `SUPABASE_USER` - Supabase database user
- `SUPABASE_PASSWORD` - Supabase database password
- `SUPABASE_HOST` - Supabase database host
- `SUPABASE_PORT` - Supabase database port (usually 5432)
- `SUPABASE_DBNAME` - Supabase database name

**API Keys:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `COHERE_API_KEY` - Your Cohere API key (optional)

**Application Configuration:**
- `EMBEDDING_PROVIDER` - Set to "openai" (default)
- `EMBEDDING_MODEL` - Set to "text-embedding-ada-002" (default)
- `VECTOR_STORE_TYPE` - Set to "faiss" (default)
- `TOP_K` - Set to "3" (default)
- `SIMILARITY_THRESHOLD` - Set to "0.7" (default)
- `LOG_LEVEL` - Set to "INFO" (default)

## Step 3: Deploy Using render.yaml (Recommended)

1. Push your code to your Git repository
2. In Render Dashboard, click "New +" → "Blueprint"
3. Connect your repository
4. Render will automatically detect the `render.yaml` file and create the service
5. Set the environment variables as listed above

**Note**: The `render.yaml` file includes the `PYTHONPATH` environment variable to ensure the `src` directory is properly included in the Python path.

## Step 4: Manual Deployment (Alternative)

If you prefer manual setup:

1. In Render Dashboard, click "New +" → "Web Service"
2. Connect your Git repository
3. Configure the service:
   - **Name**: `maqro-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.maqro_backend.main:app --host 0.0.0.0 --port $PORT`
4. Set all environment variables as listed above
5. Deploy

## Step 5: Verify Deployment

After deployment, your API will be available at:
- Root endpoint: `https://your-app-name.onrender.com/`
- API documentation: `https://your-app-name.onrender.com/docs`
- Alternative docs: `https://your-app-name.onrender.com/redoc`

## Troubleshooting

### Common Issues:

1. **Module not found errors**: 
   - The `PYTHONPATH` is set in the startup script to include the `src` directory
   - If you see "No module named 'maqro_rag'" errors, ensure the `src` directory is in the Python path
   - The `render.yaml` file includes `PYTHONPATH=$PYTHONPATH:./src` in the start command
2. **Database connection errors**: Ensure all Supabase environment variables are correctly set
3. **API key errors**: Verify your OpenAI API key is valid and has sufficient credits
4. **Missing dependencies**: Ensure all required packages are in `requirements.txt` (including `pydantic-settings`)

### Logs:
- Check Render logs in the dashboard for detailed error messages
- The application uses loguru for structured logging

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SUPABASE_DB_URL` | Complete Supabase database URL | Yes | - |
| `SUPABASE_USER` | Database username | Yes* | - |
| `SUPABASE_PASSWORD` | Database password | Yes* | - |
| `SUPABASE_HOST` | Database host | Yes* | - |
| `SUPABASE_PORT` | Database port | No | 5432 |
| `SUPABASE_DBNAME` | Database name | Yes* | - |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `COHERE_API_KEY` | Cohere API key | No | - |
| `EMBEDDING_PROVIDER` | Embedding provider | No | openai |
| `EMBEDDING_MODEL` | Embedding model | No | text-embedding-ada-002 |
| `VECTOR_STORE_TYPE` | Vector store type | No | faiss |
| `TOP_K` | Number of results to return | No | 3 |
| `SIMILARITY_THRESHOLD` | Similarity threshold | No | 0.7 |
| `LOG_LEVEL` | Logging level | No | INFO |

*Required if `SUPABASE_DB_URL` is not provided

## API Endpoints

Your deployed API will have the following endpoints:
- `GET /` - Health check and API info
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation
- `GET /api/...` - All your API routes

## Cost Considerations

- Render's free tier includes 750 hours per month
- After free tier, costs start at $7/month for the starter plan
- Consider upgrading if you need more resources or uptime 