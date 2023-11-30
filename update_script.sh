# File to store project directory and venv flag
config_file="/etc/.project_config"

# Function to prompt user for project directory
get_project_info() {
    read -p "Enter the project directory: " project_dir
    read -p "Does the project directory already contain a virtual environment? (y/n): " has_venv
    echo "$project_dir|$has_venv" > "$config_file"
}



# Check if the project information is saved, otherwise ask the user
if [ -f "$config_file" ]; then
    IFS='|' read -r project_dir has_venv < "$config_file"
    echo $project_dir
    echo $has_venvS
else
    get_project_info
fi


# Log file path
log_file="/var/log/update_script.log"

# Find the configuration file under the 'config' directory
config_dir="$project_dir/config/"
ini_file="$(find "$config_dir" -maxdepth 1 -type f -iname "*.ini" -print -quit)"

# Check if the parameters.ini file was found
if [ -z "$ini_file" ]; then
    echo "Error: No configuration file (*.ini) found in the 'config' directory. Please check your repository."
    exit 1
fi

# Back up the parameters.ini file
backup_dir="/opt/backup"

# Check if the backup directory exists, if not, create it
if [ ! -d "$backup_dir" ]; then
    sudo mkdir -p "$backup_dir"
fi
backup_file="$backup_dir/parameters_backup.ini"

# Copy the parameters.ini file to the backup directory
sudo cp "$ini_file" "$backup_file"

# Parse the parameters.ini file to get the values
mid_server=$(awk -F "=" '/^MID_SERVER/ {print $2}' "$ini_file")

# Ensure you are on the main branch
git checkout api-fixes

# Discard local changes and reset to the remote main branch
git fetch origin api-fixes
git reset --hard origin/api-fixes

# Activate virtual environment if it exists
if [ "$has_venv" = "y" ]; then
    source "$project_dir/venv/bin/activate"
else
    # Create and activate virtual environment if it doesn't exist
    python3 -m venv "$project_dir/venv"
    source "$project_dir/venv/bin/activate"
fi

# Install Python dependencies
pip install -r requirements.txt

# Copy the 'config' directory to /opt/
sudo cp -a "$config_dir" /opt/

sudo cp $project_dir/producer.service /etc/systemd/system/
sudo cp $project_dir/consumer.service /etc/systemd/system/

# Reload systemd to pick up changes
sudo systemctl daemon-reload

# Restart your services and log the output
sudo systemctl restart producer.service > "$log_file" 2>&1
sudo systemctl restart consumer.service >> "$log_file" 2>&1

# Check the status of the services
producer_status=$(sudo systemctl is-active producer.service)
consumer_status=$(sudo systemctl is-active consumer.service)

# Deactivate virtual environment
deactivate

# Print the status message
if [ "$producer_status" = "active" ] && [ "$consumer_status" = "active" ]; then
    echo "All services are up."
    echo "MID Server: $mid_server"
else
    echo "Something went wrong. Check the status of your services. See the log file for details: $log_file"
fi

