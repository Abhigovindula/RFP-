import pandas as pd
import sqlite3

# Load the uploaded CSV file
file_path = r'C:\Users\ABHI\OneDrive\Desktop\Booking-Platform-Project-\train\train_data_with_fares.csv'
df = pd.read_csv(file_path)

# Display the first few rows and the column names to inspect the data
print("First few rows of the DataFrame:")
print(df.head())
print("\nColumn Names Before Cleaning:")
print(df.columns)

# Clean up column names and convert them to lowercase for consistency
df.columns = [col.strip().replace(" ", "_").replace(".", "").lower() for col in df.columns]

print("\nColumn Names After Cleaning:")
print(df.columns)  # Display cleaned column names to see the actual names

# Check for the presence of 'islno' in the columns
if 'islno' not in df.columns:
    print("\nError: 'islno' column not found. Available columns are:", df.columns)
else:
    # Remove extra quotes from string columns and replace NaN values
    df = df.apply(lambda x: x.str.strip().replace("'", "") if x.dtype == "object" else x)
    df = df.fillna('')

    # Explicitly convert columns to appropriate data types
    df['islno'] = pd.to_numeric(df['islno'], errors='coerce').fillna(0).astype(int)
    df['distance'] = pd.to_numeric(df['distance'], errors='coerce').fillna(0).astype(int)
    df['general_fare'] = pd.to_numeric(df['general_fare'], errors='coerce').fillna(0).astype(int)
    df['sleeper_fare'] = pd.to_numeric(df['sleeper_fare'], errors='coerce').fillna(0).astype(int)
    df['ac_fare'] = pd.to_numeric(df['ac_fare'], errors='coerce').fillna(0).astype(int)

    # Connect to the database
    conn = sqlite3.connect('trains.db')
    cursor = conn.cursor()

    # Create the train_schedule table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS train_schedule (
        Train_No TEXT,
        Train_Name TEXT,
        ISLNO INTEGER,
        Station_Code TEXT,
        Station_Name TEXT,
        Arrival_Time TEXT,
        Departure_Time TEXT,
        Distance INTEGER,
        Source_Station_Code TEXT,
        Source_Station_Name TEXT,
        Destination_Station_Code TEXT,
        Destination_Station_Name TEXT,
        General_Fare INTEGER,
        Sleeper_Fare INTEGER,
        AC_Fare INTEGER
    );
    """

    cursor.execute(create_table_query)

    # Clear any existing data to avoid duplicates
    cursor.execute("DELETE FROM train_schedule;")

    # Insert data into the table
    df.to_sql('train_schedule', conn, if_exists='append', index=False)

    # Commit and close connection
    conn.commit()
    conn.close()

    # Verify the import by checking the number of rows inserted
    conn = sqlite3.connect('trains.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM train_schedule;")
    row_count = cursor.fetchone()[0]

    conn.close()

    print(f"Rows Inserted: {row_count}")