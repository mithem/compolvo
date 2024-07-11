#!/bin/bash
# Define the Docker config file path
CONFIG_FILE="$HOME/.docker/config.json"

# Check if the config file exists
if [ -f "$CONFIG_FILE" ]; then
    # Read the existing config
    CONFIG=$(cat "$CONFIG_FILE")
else
    # If not, create an empty JSON object
    CONFIG="{}"
fi

# Use jq to add or update the license key in the config
UPDATED_CONFIG=$(echo "$CONFIG" | jq --arg license "$COMPOLVO_LICENSE_KEY" '.proLicense = $license')

# Write the updated config back to the file
echo "$UPDATED_CONFIG" > "$CONFIG_FILE"

echo "Docker Pro license key added to $CONFIG_FILE"