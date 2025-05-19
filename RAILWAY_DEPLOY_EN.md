# Deploying the Optimizer Bot to Railway

This document contains detailed instructions for deploying the Windows optimization bot to the Railway platform, including solutions for the known issue with the `proxies` parameter in the Anthropic API.

## Prerequisites

- [Railway](https://railway.app/) account
- Anthropic API key (for Claude)
- Telegram Bot API token

## Deployment Steps

### 1. Project Preparation

1. Ensure all necessary files are present in your repository:
   - `optimization_bot.py` - main bot file
   - `safe_anthropic.py` - wrapper to solve the proxies issue
   - `requirements.txt` - dependencies list
   - `railway.json` - Railway configuration

2. Verify the content of `railway.json`:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "numReplicas": 1,
       "sleepApplication": false,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10,
       "startCommand": "python safe_anthropic.py && python optimization_bot.py"
     }
   }
   ```

3. Check that the correct version of the Anthropic library is specified in `requirements.txt`:
   ```
   anthropic==0.19.0
   ```

### 2. Deploy via Railway Web Interface

1. Log in to your Railway account
2. Click the "New Project" button
3. Choose "Deploy from GitHub repo" and connect your repository
4. After creating the project, go to the "Variables" section
5. Add the following environment variables:
   - `TELEGRAM_TOKEN`: your Telegram bot token
   - `ANTHROPIC_API_KEY`: your Anthropic API key
   - `RAILWAY_ENVIRONMENT`: `production`

### 3. Deploy via CLI

Alternatively, you can deploy via command line:

1. Install the Railway CLI: 
   ```
   npm i -g @railway/cli
   ```

2. Log in to your account: 
   ```
   railway login
   ```

3. Link your local directory to a new project: 
   ```
   railway init
   ```

4. Add environment variables:
   ```
   railway variables set TELEGRAM_TOKEN=your_bot_token
   railway variables set ANTHROPIC_API_KEY=your_api_key
   railway variables set RAILWAY_ENVIRONMENT=production
   ```

5. Deploy:
   ```
   railway up
   ```

## Solving the proxies Parameter Issue

When working with the Anthropic API on Railway, you might encounter this error:
```
ERROR: __init__() got an unexpected keyword argument 'proxies'
```

This happens because Railway automatically adds a `proxies` parameter to HTTP clients, but Anthropic library version 0.19.0 doesn't support this parameter.

### How Our Solution Works:

1. The `safe_anthropic.py` file intercepts and removes the `proxies` parameter during Anthropic client initialization
2. The `railway.json` file specifies a command to run `safe_anthropic.py` before the main bot
3. The `optimization_bot.py` uses this safe wrapper instead of directly importing Anthropic

### Checking Logs

If you encounter issues, check the logs in the Railway console. If the `proxies` error still appears, ensure that:

1. The application starts via the command in `railway.json`
2. The `optimization_bot.py` uses the import `import safe_anthropic as anthropic`
3. The Anthropic library version in `requirements.txt` is 0.19.0

## Additional Resources

- [Test of all approaches to solving the issue](test_all_fixes.py)
- [Railway Documentation](https://docs.railway.app/)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference/) 