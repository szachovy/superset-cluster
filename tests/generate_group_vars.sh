#!/bin/bash

cp ../src/defaults.yml ./testsuite/group_vars/testing.yml

# Output file
output_file="./testsuite/group_vars/testing.yml"

# Temporary file to store extracted defaults
temp_file="defaults.tmp"

# Ensure temp file is empty
> "$temp_file"

# Extract default values from variables.tf
while IFS= read -r line; do
    # Check for variable block start
    if [[ $line =~ ^variable ]]; then
        var_name=$(echo "$line" | grep -oP 'variable\s+"\K\w+')
    fi
    
    # Check for default value
    if [[ $line =~ default ]]; then
        default_value=$(echo "$line" | grep -oP 'default\s+=\s+\K.*')
        # Remove surrounding quotes from default value if present
        default_value=$(echo "$default_value" | sed -e 's/^"//' -e 's/"$//')
        echo "$var_name: $default_value" >> "$temp_file"
    fi
done < ./setup/variables.tf

# Write to YAML file with proper formatting
echo "mysql_password: $(openssl rand -base64 12)" >> "$output_file"
echo "superset_password: $(openssl rand -base64 12)" >> "$output_file"
while IFS= read -r line; do
    var_name=$(echo "$line" | cut -d':' -f1)
    case $var_name in
        node_version|subnet|gateway)
            continue ;;
        *)
            default_value=$(echo "$line" | cut -d':' -f2- | xargs)
            # Check if the value is a number or a string
            if [[ $default_value =~ ^[0-9]+$ ]]; then
                echo "$var_name: $default_value" >> "$output_file"
            else
                echo "$var_name: \"$default_value\"" >> "$output_file"
            fi ;;
    esac
done < "$temp_file"

# Cleanup
rm "$temp_file"

echo "defaults.yaml has been generated."
