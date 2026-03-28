'''
This file is used to perform first time setup of ARIA.

Main responsibilities:

Collects model provider, credentials, and user profile.
Sets host, port, paths, intervals
Writes `.env`
validate env vars
inits directories
check deps
'''

import os
import sys
from dotenv import set_key
from pathlib import Path
import pyfiglet

def generate_env_file(provider:str, api_key:str, host:str, port:str, tavily_key:str, user:str):
    dotenv_path = Path('.env')
    dotenv_path.touch(exist_ok=True)

    # Static Strands framework setting — skips tool confirmation prompts at runtime
    set_key(dotenv_path, "BYPASS_TOOL_CONSENT", "True")
    set_key(dotenv_path, "PROVIDER", provider)
    if api_key:
        set_key(dotenv_path, "ANTHROPIC_API_KEY", api_key)
    set_key(dotenv_path, "HOST", host)
    set_key(dotenv_path, "PORT", port)
    set_key(dotenv_path, "TAVILY_API_KEY", tavily_key)
    set_key(dotenv_path, "USER_ID", user)

def ask_user(question: str, default=None, choices=None, required=True):
    while True:
        hint = f" [{default}]" if default else ""
        if choices:
            hint += f" ({'/'.join(choices)})"
        raw = input(f"{question}{hint}: ").strip()
        value = raw or default
        if not value and required:
            print("  Required — please enter a value.")
            continue
        if choices and value.lower() not in choices:
            print(f"  Must be one of: {', '.join(choices)}")
            continue
        return value

def run_setup():
    art = pyfiglet.figlet_format("ARIA", font="bulbhead")
    greeting = f"\033[0;35m{art}\033[0m"
    print(greeting)
    #temp
    api_key=None
    try:
        provider = ask_user("Which model provider would you like to use?\n", default="bedrock", choices=["api", "bedrock", "ollama"])
        if provider == "api":
            api_key = ask_user("Enter your Anthropic API key:\n")
        host = ask_user("Pick The ARIA Server Host:\n", default="localhost")
        port = ask_user("Pick The ARIA Server Port:\n", default="65535")
        tavily_key = ask_user("Enter your Tavily API key:\n")
        user = ask_user("What should I call you?\n")

        generate_env_file(provider=provider, api_key=api_key, host=host, port=port, tavily_key=tavily_key, user=user)

        print("\033[32m.env file created successfully!")
        print("\n\033[32mSetup complete. Run 'aria serve' to start.")
    except (KeyboardInterrupt, EOFError):
        print("\n\033[31mSetup cancelled.")
        sys.exit(1)

if __name__ == "__main__":
    run_setup()