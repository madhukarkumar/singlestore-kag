#!/bin/bash

# Exit on error
set -e

# Set up environment
REPO_PATH="/Users/madhukarkumar/Dropbox/madhukar/git_repos/singlestore-kag"
cd "$REPO_PATH"

# Function to create a new terminal window running a command
create_terminal_window() {
    local title="$1"
    local command="$2"
    
    # Create the full command with environment setup
    local full_command="cd $REPO_PATH && source venv/bin/activate && export PYTHONPATH=$REPO_PATH:\$PYTHONPATH && echo '=== $title ===' && $command"
    
    # Use osascript to open a new terminal and run the command
    osascript <<EOF
        tell application "Terminal"
            activate
            do script "$full_command"
        end tell
EOF
    
    sleep 2
}

# Kill existing processes
echo "Stopping existing services..."
pkill -f "celery -A tasks worker" || true
pkill -f "uvicorn api:app" || true
sleep 2

# Restart Redis
echo "Restarting Redis..."
brew services restart redis
sleep 2
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Error: Redis failed to start"
    exit 1
fi
echo "Redis started successfully"

# Start Celery Worker
echo "Starting Celery Worker..."
create_terminal_window "Celery Worker" "celery -A tasks worker --loglevel=info"

# Start FastAPI Backend
echo "Starting FastAPI Backend..."
create_terminal_window "FastAPI" "uvicorn api:app --reload"

echo "All services started!"
echo "Check the Terminal windows for each service's output"
