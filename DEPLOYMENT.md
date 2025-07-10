# Deployment Guide

## Railway Deployment

### Prerequisites
- Node.js >=22.0.0
- Python >=3.9
- All environment variables configured

### Railway Configuration
The project includes a `railway.toml` configuration file that defines:
- Build commands for both Node.js and Python dependencies
- Start command using the web UI
- Health check configuration
- Environment variable mapping

### Environment Variables Required
Ensure the following environment variables are set in Railway:

#### Essential
- `OPENAI_API_KEY` - OpenAI API key for LLM access
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models
- `DATABASE_URL` - PostgreSQL connection string
- `NODE_ENV=production`

#### Optional (but recommended)
- `GROQ_API_KEY` - Groq API for faster inference
- `GOOGLE_API_KEY` - Google/Gemini API access
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key

### Deploy Steps
1. Connect your GitHub repository to Railway
2. Configure environment variables in Railway dashboard
3. Deploy using the `railway.toml` configuration
4. Monitor logs for successful startup

## Docker Deployment

The project includes a comprehensive `Dockerfile` for containerized deployment:

```bash
# Build the image
docker build -t gary-zero .

# Run with environment file
docker run -p 50001:50001 --env-file .env gary-zero
```

## Local Development

### Setup
1. Install Node.js >=22.0.0 (check `.nvmrc`)
2. Install Python >=3.9
3. Install dependencies:
   ```bash
   npm install
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
4. Copy `.env.example` to `.env` and configure
5. Start the application:
   ```bash
   npm start
   # or
   python run_ui.py
   ```

### Development Tools
- **ESLint**: `npm run lint`
- **Biome**: `npm run biome:check`
- **Ruff**: `ruff check .`
- **Tests**: `npm test`
- **TypeScript**: `npm run tsc:check`