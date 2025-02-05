#!/usr/bin/fish


# Define paths
set SOURCE_PROJECT "/home/rupel/Documents/babbling_melons/synced"
set VENV_PATH "$SOURCE_PROJECT/venv"
set REMOTE_HOST "feetfirst"

# Step 1: Check for virtual environment and generate requirements.txt
if test -d $VENV_PATH
    echo "Generating requirements.txt from virtual environment..."
    # Activate the virtual environment
    source $VENV_PATH/bin/activate.fish
    # Generate requirements.txt
    pip freeze > "$SOURCE_PROJECT/requirements.txt"
else
    echo "Virtual environment not found at $VENV_PATH. Skipping requirements.txt generation."
end

# Sync project folder
    echo "Syncing project folder"
	rsync -avz --delete --relative $SOURCE_PROJECT $REMOTE_HOST:/

# Rebuild virtual environment on the remote host
echo "Updating or rebuilding virtual environment on the remote host..."
ssh $REMOTE_HOST "
    bash -c '
    # Ensure virtual environment exists (idempotent)
    python3 -m venv $VENV_PATH 
    
    # Update dependencies in the venv
    pip install --upgrade --prefix $VENV_PATH -r $SOURCE_PROJECT/requirements.txt
    '
"


