import random
from datetime import datetime, timedelta

# Hardcoded data from your schema
items_data = [
    (1, 0.00), (2, 0.00), (3, 0.00), (4, 0.00), (5, 0.00), (6, 0.00), (7, 0.00), (8, 0.00), (9, 0.00), (10, 0.00), (11, 0.00), # Milk Tea
    (12, 0.00), (13, 0.00), (14, 0.00), (15, 0.00), (16, 0.00), (17, 0.00), (18, 0.00), (19, 0.00), # Coffee
    (20, 0.00), (21, 0.00), (22, 0.00), (23, 0.00), (24, 0.00), (25, 0.00), (26, 0.00), (27, 0.00), (28, 0.00), (29, 0.00), # Fruit Tea
    (30, 0.00), (31, 0.00), (32, 0.00), (33, 0.00), (34, 0.00), (35, 0.00), (36, 0.00), (37, 0.00), (38, 0.00), (39, 0.00), (40, 0.00) # Praf
]

sizes_data = [
    (1, 29.00), # Medio
    (2, 39.00)  # Grande
]

# Map size_id to price for easy lookup
size_price_map = {size_id: price for size_id, price in sizes_data}

start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 5, 4, 23, 59, 59) # Include the whole day of May 4

num_transactions = 500

# Generate random datetimes within the range
time_range_seconds = int((end_date - start_date).total_seconds())
random_seconds = [random.randint(0, time_range_seconds) for _ in range(num_transactions)]

# Convert seconds offset to actual datetimes and sort descending
dates = [start_date + timedelta(seconds=sec) for sec in random_seconds]
dates.sort(reverse=True) # Sort in descending order

transactions_sql_values = []
transaction_items_sql_values = []

# Simulate transaction_id AUTO_INCREMENT for linking items during generation
# The actual IDs in the database will depend on the last inserted ID + AUTO_INCREMENT
# We will rely on the order of insertion to link transactions and items.
simulated_transaction_id_counter = 1 # Start counter for ordering items

for transaction_date in dates:
    # Format transaction number as TXNYYYYMMDDSS
    transaction_number = f"TXN{transaction_date.strftime('%Y%m%d%S')}"

    items_in_transaction = random.randint(1, 5) # 1 to 5 items per transaction
    current_transaction_total = 0
    current_transaction_item_details = []

    for _ in range(items_in_transaction):
        item_id = random.choice(items_data)[0]
        size_id, size_price = random.choice(sizes_data)
        quantity = random.randint(1, 3) # 1 to 3 quantity for each item line
        item_total_price = round(quantity * size_price, 2)
        current_transaction_total = round(current_transaction_total + item_total_price, 2)

        current_transaction_item_details.append({
            # We don't include transaction_id here yet, will add it in the final output structure
            'item_id': item_id,
            'size_id': size_id,
            'quantity': quantity,
            'total_price': item_total_price
        })

    # Generate customer payment (at least total_amount, plus a random extra)
    extra_payment = random.uniform(0, max(50.00, current_transaction_total * 0.3)) # Pay at least total, up to 30% more or 50 extra
    customer_payment = round(current_transaction_total + extra_payment, 2)
    # Ensure payment is explicitly >= total_amount
    if customer_payment < current_transaction_total:
         customer_payment = current_transaction_total + random.uniform(1.00, 10.00) # Add a small random extra if needed
         customer_payment = round(customer_payment, 2)


    change_amount = round(customer_payment - current_transaction_total, 2)
    if change_amount < 0: # Should not happen with the logic above, but as a safeguard
        change_amount = 0

    # Add the transaction details to the list
    transactions_sql_values.append(
        f"('{transaction_date.strftime('%Y-%m-%d %H:%M:%S')}', "
        f"'{transaction_number}', "
        f"{current_transaction_total:.2f}, "
        f"{customer_payment:.2f}, "
        f"{change_amount:.2f}, "
        f"{2})" # user_id is 2 as per your example data
    )

    # Add the item details for this transaction to the main items list
    # We add them in the order the transactions were generated (which is descending date order)
    for item in current_transaction_item_details:
        # The actual transaction_id will correspond to the order of the transaction INSERT
        transaction_items_sql_values.append(
             f"(/* AUTO_GENERATED_TXN_ID */, {item['item_id']}, {item['size_id']}, {item['quantity']}, {item['total_price']:.2f})"
         )

    simulated_transaction_id_counter += 1


# --- Write the data to a SQL file ---
file_name = "generated_pos_data.sql"
with open(file_name, "w") as f:
    f.write("USE DB_POSONGBATO;\n\n")

    f.write("-- Inserting 500 transactions (sorted by date descending)\n")
    f.write("-- The actual transaction_id will be auto-generated starting from the next available ID\n")
    f.write("INSERT INTO tbl_transactions (transaction_date, transaction_number, total_amount, customer_payment, change_amount, user_id) VALUES\n")
    f.write(",\n".join(transactions_sql_values) + ";\n\n")

    f.write("-- Inserting transaction items\n")
    f.write("-- IMPORTANT: The first value in each row below ('/* AUTO_GENERATED_TXN_ID */') is a placeholder.\n")
    f.write("-- You need to replace it with the actual auto-generated transaction_id.\n")
    f.write("-- The item rows are ordered to correspond to the transaction rows inserted immediately above.\n")
    f.write("-- For example, if the first transaction inserted got transaction_id X, replace '/* AUTO_GENERATED_TXN_ID */' with X for the first block of item rows.\n")
    f.write("-- If inserting these values directly after the transactions using a client that guarantees sequential AUTO_INCREMENT,\n")
    f.write("-- you might be able to simplify the insert or use LAST_INSERT_ID() or similar database-specific functions in a script.\n")
    f.write("INSERT INTO tbl_transactionItems (transaction_id, item_id, size_id, quantity, total_price) VALUES\n")
    f.write(",\n".join(transaction_items_sql_values) + ";\n")

print(f"Generated data for {num_transactions} transactions and their items into '{file_name}'")
print("\nInstructions:")
print(f"1. Save the code above as a Python file (e.g., `generate_data.py`).")
print(f"2. Run the script from your terminal: `python generate_data.py`")
print(f"3. This will create the file `{file_name}` in the same directory.")
print(f"4. Use a MySQL client (like MySQL Workbench, command line, or phpMyAdmin) to execute the SQL commands in `{file_name}` against your `DB_POSONGBATO` database.")
print("   - Make sure you have already created the database and tables, and inserted the initial data (login, categories, sizes, items, etc.).")
print("   - Pay close attention to the comment regarding the `transaction_id` in the `tbl_transactionItems` insert statement.")