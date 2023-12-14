#!/bin/bash

DATE=$(date "+%Y%m%d%H%M")
# Log file path
log_file="/var/log/script.log"

update_file="/opt/servicenow/mid/agent/export/update.zip"
drass_destination= $(pwd)

echo "Started sync at ${DATE}"  >> "$log_file"

# # Check if the update file exists
# while [ ! -e "$update_file" ]; do
#     echo "Waiting for update file..." >> "$log_file"
#     sleep 5
# done

if [ -z "$update_file" ]; then
    echo "Error: No update file (*.zip) found in the project directory. Please check your folder." >> "$log_file"
    exit 1
fi

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

# Clean up the extracted update file if it exists
if [ -d "$temp_extracted_dir" ]; then
    rm -r "$temp_extracted_dir"
    echo "Extracted update files deleted." >> "$log_file"
fi

# Delete the update ZIP file
if [ -e "$update_file" ]; then
    rm "$update_file"
    echo "Update ZIP file deleted." >> "$log_file"
fi

echo "Update applied successfully." >> "$log_file"




