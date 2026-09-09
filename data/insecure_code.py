import subprocess

password = "admin123"

def run_command(user_input):
    subprocess.call(user_input, shell=True)

def connect_db():
    api_key = "sk-1234567890abcdef"
    return api_key