#!/bin/bash

# Get the current working directory
project_dir="$(pwd)"

# Log file path
log_file="$project_dir/update_script.log"

# Get the current local branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

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
else
    echo "Something went wrong. Check the status of your services. See the log file for details: $log_file"
fi

