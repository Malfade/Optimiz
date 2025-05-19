#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Railway Anthropic Proxies Issue Fixer ===${NC}"
echo -e "${BLUE}This script will test and apply the fix for the 'proxies' parameter issue${NC}"
echo

# Step 1: Check if safe_anthropic.py already exists
if [ -f "safe_anthropic.py" ]; then
    echo -e "${YELLOW}safe_anthropic.py already exists.${NC}"
else
    echo -e "${BLUE}Creating safe_anthropic.py...${NC}"
    cat > safe_anthropic.py << 'EOF'
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
EOF
    echo -e "${GREEN}safe_anthropic.py created successfully.${NC}"
fi

# Step 2: Create test script
echo -e "${BLUE}Creating test script...${NC}"
cat > test_fix.py << 'EOF'
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_anthropic")

# Test both regular anthropic and safe_anthropic
def test_standard_anthropic():
    try:
        import anthropic
        logger.info("Testing standard Anthropic client with proxies parameter...")
        api_key = os.environ.get("ANTHROPIC_API_KEY", "dummy_key_for_testing")
        client = anthropic.Anthropic(api_key=api_key, proxies={"http": "dummy"})
        logger.info("PASS: Standard Anthropic client created with proxies parameter")
        return True
    except Exception as e:
        logger.error(f"FAIL: Standard Anthropic client error: {str(e)}")
        return False

def test_safe_anthropic():
    try:
        import safe_anthropic as anthropic
        logger.info("Testing safe_anthropic wrapper...")
        api_key = os.environ.get("ANTHROPIC_API_KEY", "dummy_key_for_testing")
        client = anthropic.Anthropic(api_key=api_key, proxies={"http": "dummy"})
        logger.info("PASS: Client created with safe_anthropic wrapper")
        return True
    except Exception as e:
        logger.error(f"FAIL: safe_anthropic error: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting tests...")
    standard_result = test_standard_anthropic()
    safe_result = test_safe_anthropic()
    
    print("\n--- TEST RESULTS ---")
    print(f"Standard Anthropic: {'✅ PASS' if standard_result else '❌ FAIL'}")
    print(f"safe_anthropic:     {'✅ PASS' if safe_result else '❌ FAIL'}")
    
    if not standard_result and safe_result:
        print("\n✅ The safe_anthropic wrapper is working as expected!")
        print("   This confirms the Railway proxies issue is present and the fix is working.")
    elif standard_result:
        print("\n⚠️ The standard Anthropic client works with proxies parameter.")
        print("   You might be using a newer version of the Anthropic library that already supports proxies.")
    else:
        print("\n❌ Both tests failed. There might be other issues with your setup.")
    
    sys.exit(0 if safe_result else 1)
EOF
echo -e "${GREEN}Test script created successfully.${NC}"

# Step 3: Check railway.json file
if [ -f "railway.json" ]; then
    echo -e "${BLUE}Checking railway.json...${NC}"
    if grep -q "safe_anthropic.py" railway.json; then
        echo -e "${GREEN}railway.json already contains reference to safe_anthropic.py.${NC}"
    else
        echo -e "${YELLOW}Updating railway.json...${NC}"
        # Backup the original file
        cp railway.json railway.json.bak
        
        # Process railway.json to update startCommand
        python3 -c '
import json
import re

try:
    with open("railway.json", "r") as f:
        data = json.load(f)
    
    if "deploy" in data and "startCommand" in data["deploy"]:
        original_cmd = data["deploy"]["startCommand"]
        
        # If there is already a command that runs python scripts
        if "python" in original_cmd:
            # Find the main python script being run
            matches = re.findall(r"python\s+([^&;\s]+\.py)", original_cmd)
            if matches:
                main_script = matches[-1]  # Take the last python script in the command
                # Replace with our fixed command
                new_cmd = f"python safe_anthropic.py && python {main_script}"
                data["deploy"]["startCommand"] = new_cmd
                print(f"Updated command from {original_cmd} to {new_cmd}")
            else:
                # If we cant find a clear python script, prepend our fix
                data["deploy"]["startCommand"] = f"python safe_anthropic.py && {original_cmd}"
                print(f"Prepended safe_anthropic.py to existing command")
        else:
            # If there is no python command, add ours
            data["deploy"]["startCommand"] = f"python safe_anthropic.py && {original_cmd}"
            print(f"Added safe_anthropic.py before existing command")
            
        with open("railway.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Successfully updated railway.json")
    else:
        print("Could not find startCommand in railway.json")
        
except Exception as e:
    print(f"Error updating railway.json: {str(e)}")
'
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}railway.json updated successfully.${NC}"
        else
            echo -e "${RED}Failed to update railway.json. Please update it manually.${NC}"
            echo -e "${YELLOW}Your command should include: python safe_anthropic.py && python your_main_script.py${NC}"
        fi
    fi
else
    echo -e "${YELLOW}railway.json not found. Creating a basic template...${NC}"
    cat > railway.json << 'EOF'
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
EOF
    echo -e "${GREEN}Basic railway.json created. Please edit it to match your main script name.${NC}"
fi

# Step 4: Run the test
echo -e "\n${BLUE}Running tests...${NC}"
python test_fix.py

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}All set! Your project is now protected against the Railway proxies issue.${NC}"
    echo -e "${BLUE}Make sure your code imports Anthropic like this:${NC}"
    echo -e "${YELLOW}import safe_anthropic as anthropic${NC}"
    echo -e "\n${BLUE}Deploy command: railway up${NC}"
else
    echo -e "\n${RED}Test failed. Please check the logs above for details.${NC}"
fi

echo -e "\n${BLUE}=== Script completed ===${NC}" 