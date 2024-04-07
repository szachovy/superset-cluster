#!/bin/bash

# Define the filename for the SQL file
sql_file="large_row_data.sql"

# Define the table name
table_name="LargeRow"

# Define the number of rows to generate
num_rows=10000

# Generate the SQL file
echo "CREATE TABLE $table_name (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    val FLOAT
);" > "$sql_file"

echo "INSERT INTO $table_name (val) VALUES" >> "$sql_file"

# Generate 1 million random float values and append them to the SQL file
for ((i=1; i<=$num_rows; i++))
do
    # Generate a random float value between 0 and 1
    float_value=$(awk -v seed="$RANDOM" 'BEGIN{srand(seed); printf "%.6f\n", rand()}')
    
    # Append the insert statement to the SQL file
    echo "($float_value)," >> "$sql_file"
done

# Remove the trailing comma from the last insert statement
sed -i '$ s/.$//' "$sql_file"

# Add a semicolon to the last line to terminate the SQL statement
echo ";" >> "$sql_file"

echo "SQL file $sql_file created successfully."
