@echo off
chcp 65001 >nul
title Railway Anthropic Proxies Issue Fixer

echo === Railway Anthropic Proxies Issue Fixer ===
echo This script will test and apply the fix for the 'proxies' parameter issue
echo.

REM Step 1: Check if safe_anthropic.py already exists
if exist "safe_anthropic.py" (
    echo safe_anthropic.py already exists.
) else (
    echo Creating safe_anthropic.py...
    
    echo import logging > safe_anthropic.py
    echo import anthropic >> safe_anthropic.py
    echo from anthropic._client import SyncHttpxClientWrapper >> safe_anthropic.py
    echo. >> safe_anthropic.py
    echo # Set up logging >> safe_anthropic.py
    echo logging.basicConfig(level=logging.INFO) >> safe_anthropic.py
    echo logger = logging.getLogger("safe_anthropic") >> safe_anthropic.py
    echo. >> safe_anthropic.py
    echo # Store the original __init__ method >> safe_anthropic.py
    echo original_init = SyncHttpxClientWrapper.__init__ >> safe_anthropic.py
    echo. >> safe_anthropic.py
    echo # Define the patched __init__ method >> safe_anthropic.py
    echo def patched_init(self, *args, **kwargs): >> safe_anthropic.py
    echo     # Log the original kwargs for debugging >> safe_anthropic.py
    echo     logger.info(f"Original kwargs: {kwargs}") >> safe_anthropic.py
    echo. >> safe_anthropic.py
    echo     # Remove 'proxies' parameter if present >> safe_anthropic.py
    echo     if 'proxies' in kwargs: >> safe_anthropic.py
    echo         logger.info("Removing 'proxies' parameter from kwargs") >> safe_anthropic.py
    echo         kwargs.pop('proxies') >> safe_anthropic.py
    echo. >> safe_anthropic.py
    echo     # Log the modified kwargs >> safe_anthropic.py
    echo     logger.info(f"Modified kwargs: {kwargs}") >> safe_anthropic.py
    echo. >> safe_anthropic.py
    echo     # Call the original __init__ method with the modified kwargs >> safe_anthropic.py
    echo     original_init(self, *args, **kwargs) >> safe_anthropic.py
    echo. >> safe_anthropic.py
    echo # Apply the patch >> safe_anthropic.py
    echo SyncHttpxClientWrapper.__init__ = patched_init >> safe_anthropic.py
    echo. >> safe_anthropic.py
    echo logger.info("Successfully patched Anthropic client to remove 'proxies' parameter") >> safe_anthropic.py
    echo. >> safe_anthropic.py
    echo # Export the same interface as the original anthropic module >> safe_anthropic.py
    echo from anthropic import * >> safe_anthropic.py
    
    echo safe_anthropic.py created successfully.
)

REM Step 2: Create test script
echo Creating test script...

echo import os > test_fix.py
echo import logging >> test_fix.py
echo import sys >> test_fix.py
echo. >> test_fix.py
echo # Configure logging >> test_fix.py
echo logging.basicConfig(level=logging.INFO, format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s') >> test_fix.py
echo logger = logging.getLogger("test_anthropic") >> test_fix.py
echo. >> test_fix.py
echo # Test both regular anthropic and safe_anthropic >> test_fix.py
echo def test_standard_anthropic(): >> test_fix.py
echo     try: >> test_fix.py
echo         import anthropic >> test_fix.py
echo         logger.info("Testing standard Anthropic client with proxies parameter...") >> test_fix.py
echo         api_key = os.environ.get("ANTHROPIC_API_KEY", "dummy_key_for_testing") >> test_fix.py
echo         client = anthropic.Anthropic(api_key=api_key, proxies={"http": "dummy"}) >> test_fix.py
echo         logger.info("PASS: Standard Anthropic client created with proxies parameter") >> test_fix.py
echo         return True >> test_fix.py
echo     except Exception as e: >> test_fix.py
echo         logger.error(f"FAIL: Standard Anthropic client error: {str(e)}") >> test_fix.py
echo         return False >> test_fix.py
echo. >> test_fix.py
echo def test_safe_anthropic(): >> test_fix.py
echo     try: >> test_fix.py
echo         import safe_anthropic as anthropic >> test_fix.py
echo         logger.info("Testing safe_anthropic wrapper...") >> test_fix.py
echo         api_key = os.environ.get("ANTHROPIC_API_KEY", "dummy_key_for_testing") >> test_fix.py
echo         client = anthropic.Anthropic(api_key=api_key, proxies={"http": "dummy"}) >> test_fix.py
echo         logger.info("PASS: Client created with safe_anthropic wrapper") >> test_fix.py
echo         return True >> test_fix.py
echo     except Exception as e: >> test_fix.py
echo         logger.error(f"FAIL: safe_anthropic error: {str(e)}") >> test_fix.py
echo         return False >> test_fix.py
echo. >> test_fix.py
echo if __name__ == "__main__": >> test_fix.py
echo     logger.info("Starting tests...") >> test_fix.py
echo     standard_result = test_standard_anthropic() >> test_fix.py
echo     safe_result = test_safe_anthropic() >> test_fix.py
echo. >> test_fix.py
echo     print("\n--- TEST RESULTS ---") >> test_fix.py
echo     print(f"Standard Anthropic: {'✅ PASS' if standard_result else '❌ FAIL'}") >> test_fix.py
echo     print(f"safe_anthropic:     {'✅ PASS' if safe_result else '❌ FAIL'}") >> test_fix.py
echo. >> test_fix.py
echo     if not standard_result and safe_result: >> test_fix.py
echo         print("\n✅ The safe_anthropic wrapper is working as expected!") >> test_fix.py
echo         print("   This confirms the Railway proxies issue is present and the fix is working.") >> test_fix.py
echo     elif standard_result: >> test_fix.py
echo         print("\n⚠️ The standard Anthropic client works with proxies parameter.") >> test_fix.py
echo         print("   You might be using a newer version of the Anthropic library that already supports proxies.") >> test_fix.py
echo     else: >> test_fix.py
echo         print("\n❌ Both tests failed. There might be other issues with your setup.") >> test_fix.py
echo. >> test_fix.py
echo     sys.exit(0 if safe_result else 1) >> test_fix.py

echo Test script created successfully.

REM Step 3: Check railway.json file
if exist "railway.json" (
    echo Checking railway.json...
    
    findstr /C:"safe_anthropic.py" railway.json >nul
    if %errorlevel% equ 0 (
        echo railway.json already contains reference to safe_anthropic.py.
    ) else (
        echo Updating railway.json...
        
        REM Backup the original file
        copy railway.json railway.json.bak > nul
        
        REM Create a temporary Python script to update railway.json
        echo import json > update_railway.py
        echo import re >> update_railway.py
        echo. >> update_railway.py
        echo try: >> update_railway.py
        echo     with open("railway.json", "r") as f: >> update_railway.py
        echo         data = json.load(f) >> update_railway.py
        echo. >> update_railway.py
        echo     if "deploy" in data and "startCommand" in data["deploy"]: >> update_railway.py
        echo         original_cmd = data["deploy"]["startCommand"] >> update_railway.py
        echo. >> update_railway.py
        echo         # If there is already a command that runs python scripts >> update_railway.py
        echo         if "python" in original_cmd: >> update_railway.py
        echo             # Find the main python script being run >> update_railway.py
        echo             matches = re.findall(r"python\s+([^&;\s]+\.py)", original_cmd) >> update_railway.py
        echo             if matches: >> update_railway.py
        echo                 main_script = matches[-1]  # Take the last python script in the command >> update_railway.py
        echo                 # Replace with our fixed command >> update_railway.py
        echo                 new_cmd = f"python safe_anthropic.py ^&^& python {main_script}" >> update_railway.py
        echo                 data["deploy"]["startCommand"] = new_cmd >> update_railway.py
        echo                 print(f"Updated command from {original_cmd} to {new_cmd}") >> update_railway.py
        echo             else: >> update_railway.py
        echo                 # If we cant find a clear python script, prepend our fix >> update_railway.py
        echo                 data["deploy"]["startCommand"] = f"python safe_anthropic.py ^&^& {original_cmd}" >> update_railway.py
        echo                 print(f"Prepended safe_anthropic.py to existing command") >> update_railway.py
        echo         else: >> update_railway.py
        echo             # If there is no python command, add ours >> update_railway.py
        echo             data["deploy"]["startCommand"] = f"python safe_anthropic.py ^&^& {original_cmd}" >> update_railway.py
        echo             print(f"Added safe_anthropic.py before existing command") >> update_railway.py
        echo. >> update_railway.py
        echo         with open("railway.json", "w") as f: >> update_railway.py
        echo             json.dump(data, f, indent=2) >> update_railway.py
        echo         print("Successfully updated railway.json") >> update_railway.py
        echo     else: >> update_railway.py
        echo         print("Could not find startCommand in railway.json") >> update_railway.py
        echo. >> update_railway.py
        echo except Exception as e: >> update_railway.py
        echo     print(f"Error updating railway.json: {str(e)}") >> update_railway.py
        
        python update_railway.py
        
        if %errorlevel% equ 0 (
            echo railway.json updated successfully.
            del update_railway.py
        ) else (
            echo Failed to update railway.json. Please update it manually.
            echo Your command should include: python safe_anthropic.py ^&^& python your_main_script.py
        )
    )
) else (
    echo railway.json not found. Creating a basic template...
    
    echo { > railway.json
    echo   "$schema": "https://railway.app/railway.schema.json", >> railway.json
    echo   "build": { >> railway.json
    echo     "builder": "NIXPACKS" >> railway.json
    echo   }, >> railway.json
    echo   "deploy": { >> railway.json
    echo     "numReplicas": 1, >> railway.json
    echo     "sleepApplication": false, >> railway.json
    echo     "restartPolicyType": "ON_FAILURE", >> railway.json
    echo     "restartPolicyMaxRetries": 10, >> railway.json
    echo     "startCommand": "python safe_anthropic.py ^&^& python optimization_bot.py" >> railway.json
    echo   } >> railway.json
    echo } >> railway.json
    
    echo Basic railway.json created. Please edit it to match your main script name.
)

REM Step 4: Run the test
echo.
echo Running tests...
python test_fix.py

if %errorlevel% equ 0 (
    echo.
    echo All set! Your project is now protected against the Railway proxies issue.
    echo Make sure your code imports Anthropic like this:
    echo import safe_anthropic as anthropic
    echo.
    echo Deploy command: railway up
) else (
    echo.
    echo Test failed. Please check the logs above for details.
)

echo.
echo === Script completed ===
pause 