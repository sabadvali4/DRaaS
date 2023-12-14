#!/bin/bash

update_file="/opt/servicenow/mid/agent/export/update_xxxx.zip"
drass_destination="/path/to/drass"  ##where??

# Check if the update file exists
while [ ! -e "$update_file" ]; do
    echo "Waiting for update file..."
    sleep 5
done

# Extract the contents of the update file.
temp_extracted_dir=$(mktemp -d)
unzip -q "$update_file" -d "$temp_extracted_dir"

# Update specific files in DRaaS folder
for file in "$temp_extracted_dir"*; do
    filename=$(basename "$file")
    
    # Exclude config and ini files
    if [[ "$filename" != *.config && "$filename" != *.ini ]]; then
        # Update the file in the destination folder
        cp "$file" "$drass_destination/$filename"
    fi
done

# Clean up temporary directory
rm -r "$temp_extracted_dir"

echo "Update applied successfully."




