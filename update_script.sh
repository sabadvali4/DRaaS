#!/bin/bash

# Navigate to your project directory
cd /home/devops/DRaaS

# Log file path
log_file="/home/devops/DRaaS/update_script.log"

# Fetch the latest changes from the remote repository
git fetch origin

# Get the current local branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Update the local branch with the latest changes
git pull origin $current_branch

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
