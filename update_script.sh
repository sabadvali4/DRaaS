#!/bin/bash

# Get the current working directory
project_dir="$(pwd)"

# Log file path
log_file="$project_dir/update_script.log"

# Find the configuration file under the 'config' directory
config_dir="$project_dir/config"
ini_file="$(find "$config_dir" -maxdepth 1 -type f -iname "*.ini" -print -quit)"

# Check if the parameters.ini file was found
if [ -z "$ini_file" ]; then
    echo "Error: No configuration file (*.ini) found in the 'config' directory. Please check your repository."
    exit 1
fi

# Discard local changes and reset to the remote branch
git fetch origin "$current_branch"
git reset --hard "origin/$current_branch"

# Copy the 'config' directory to /opt/
sudo cp -a config /opt/

# Restart your services and log the output
sudo systemctl restart producer.service > "$log_file" 2>&1
sudo systemctl restart consumer.service >> "$log_file" 2>&1

# Check the status of the services
producer_status=$(sudo systemctl is-active producer.service)
consumer_status=$(sudo systemctl is-active consumer.service)

# Print the status message
if [ "$producer_status" = "active" ] && [ "$consumer_status" = "active" ]; then
    echo "All services are up."
    echo "MID Server: $mid_server"
else
    echo "Something went wrong. Check the status of your services. See the log file for details: $log_file"
fi

