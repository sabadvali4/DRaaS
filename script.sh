#!/bin/bash

DATE=$(date "+%Y%m%d%H%M")
# Log file path
log_file="/var/log/script.log"

update_file="/opt/servicenow/mid/agent/export/update_xxxx.zip"
drass_destination= $(pwd)

echo "Started sync at ${DATE}"  >> "$log_file"
# Check if the update file exists
while [ ! -e "$update_file" ]; do
    echo "Waiting for update file..." >> "$log_file"
    sleep 5
done

# Extract the contents of the update file.
temp_extracted_dir=$(mktemp -d)
unzip -q "$update_file" -d "$temp_extracted_dir"
echo "extracted the folder to "$temp_extracted_dir". " >> "$log_file"

# Update specific files in DRaaS folder
for file in "$temp_extracted_dir"*; do
    filename=$(basename "$file")
    
    # Exclude config and ini files
    if [[ "$filename" != *.config && "$filename" != *.ini ]]; then
        # Update the file in the destination folder
        cp "$file" "$drass_destination/$filename"
        echo "copied the new file: "$file"." >> "$log_file"
    fi
done

# Clean up temporary directory
rm -r "$temp_extracted_dir"

echo "Update applied successfully." >> "$log_file"




