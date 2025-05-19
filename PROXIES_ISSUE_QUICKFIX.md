# Quick Fix: Anthropic Proxies Issue on Railway

If you're encountering the error `__init__() got an unexpected keyword argument 'proxies'` with Anthropic API on Railway, here's a fast solution:

## Option 1: Use the safe_anthropic wrapper (Recommended)

1. Create a file named `safe_anthropic.py` with this content:

```python
import logging
import anthropic
from anthropic._client import SyncHttpxClientWrapper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("safe_anthropic")

# Store the original __init__ method
original_init = SyncHttpxClientWrapper.__init__

# Define the patched __init__ method
def patched_init(self, *args, **kwargs):
    # Log the original kwargs for debugging
    logger.info(f"Original kwargs: {kwargs}")
    
    # Remove 'proxies' parameter if present
    if 'proxies' in kwargs:
        logger.info("Removing 'proxies' parameter from kwargs")
        kwargs.pop('proxies')
    
    # Log the modified kwargs
    logger.info(f"Modified kwargs: {kwargs}")
    
    # Call the original __init__ method with the modified kwargs
    original_init(self, *args, **kwargs)

# Apply the patch
SyncHttpxClientWrapper.__init__ = patched_init

logger.info("Successfully patched Anthropic client to remove 'proxies' parameter")

# Export the same interface as the original anthropic module
from anthropic import *
```

2. Update your `railway.json` file to run this script before your main application:

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
    "startCommand": "python safe_anthropic.py && python your_main_script.py"
  }
}
```

3. In your main code, import Anthropic through the wrapper:

```python
import safe_anthropic as anthropic

# Use anthropic as normal
client = anthropic.Anthropic(api_key=api_key)
```

## Option 2: Quick patch in your main script

If you prefer a single-file solution, add this at the top of your main script:

```python
# Patch for Railway proxies issue
import anthropic
from anthropic._client import SyncHttpxClientWrapper

original_init = SyncHttpxClientWrapper.__init__
def patched_init(self, *args, **kwargs):
    if 'proxies' in kwargs:
        kwargs.pop('proxies')
    original_init(self, *args, **kwargs)
SyncHttpxClientWrapper.__init__ = patched_init
```

## Option 3: Try/except fallback approach

Another approach is to try creating the client normally first, then fall back to a version without proxies:

```python
import anthropic

def create_client(api_key):
    try:
        # Try normal initialization
        return anthropic.Anthropic(api_key=api_key)
    except TypeError as e:
        if "unexpected keyword argument 'proxies'" in str(e):
            # Railway environment - create a custom client without proxies
            import os
            # Clear any proxy environment variables that might be set
            for var in list(os.environ.keys()):
                if 'PROXY' in var.upper() or 'HTTP_' in var.upper():
                    os.environ.pop(var, None)
            # Try again with clean environment
            return anthropic.Anthropic(api_key=api_key)
        else:
            # Different error, re-raise
            raise

# Use the safe creator
client = create_client(api_key)
```

## Testing Your Fix

To test if your fix works, create a file named `test_anthropic.py`:

```python
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_anthropic")

# Test with safe_anthropic
try:
    import safe_anthropic as anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY", "dummy_key_for_testing")
    client = anthropic.Anthropic(api_key=api_key, proxies={"http": "dummy"})
    logger.info("SUCCESS: Client created with safe_anthropic")
except Exception as e:
    logger.error(f"ERROR with safe_anthropic: {str(e)}")

# Run test: python test_anthropic.py
```

## Compatibility

This fix is specifically designed for:
- anthropic==0.19.0
- Railway deployment environment

For other versions, you may need to adjust the patch method. 