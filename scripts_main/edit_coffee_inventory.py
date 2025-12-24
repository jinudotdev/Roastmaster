# scripts_main/edit_coffee_inventory.py

import os
import pandas as pd
from scripts_utility.capture import get_validated_date, get_validated_input

INVENTORY_PATH = os.path.join("data", "coffee_inventory.csv")

def choose_inventory_entry(inventory_path=INVENTORY_PATH):
    df = load_inventory()
    if df.empty:
        return None

    print("\nAvailable Coffees in Inventory:")
    for _, row in df.iterrows():
        print(f"{row['id']}: {row['supplier']} - {row['country']} {row['region']} "
              f"({row['variety']}, {row['process_method']}) | Purchased: {row['purchase_date']}")

    choice = input("Enter ID to use (or press Enter to skip): ").strip()
    if choice and choice.isdigit():
        entry = df[df["id"] == int(choice)]
        if not entry.empty:
            return entry.iloc[0].to_dict()
    return None

def load_inventory() -> pd.DataFrame:
    if os.path.exists(INVENTORY_PATH):
        return pd.read_csv(INVENTORY_PATH)
    else:
        return pd.DataFrame(columns=[
            "id", "supplier", "country", "region",
            "altitude_meters", "variety", "process_method", "purchase_date"
        ])

def save_inventory(df: pd.DataFrame):
    os.makedirs(os.path.dirname(INVENTORY_PATH), exist_ok=True)
    df.to_csv(INVENTORY_PATH, index=False)

def list_inventory(df: pd.DataFrame):
    if df.empty:
        print("\n📂 Inventory is empty.\n")
        return
    print("\n📂 Current Coffee Inventory:")
    for _, row in df.iterrows():
        print(f"{row['id']}: {row['supplier']} - {row['country']} {row['region']} "
              f"({row['variety']}, {row['process_method']}) | Purchased: {row['purchase_date']}")
    print()

def add_entry(df: pd.DataFrame) -> pd.DataFrame:
    next_id = 1 if df.empty else df["id"].max() + 1
    print("\n➕ Add New Coffee Entry:")

    supplier = get_validated_input("Supplier: ", str)
    country = get_validated_input("Country: ", str)
    region = get_validated_input("Region: ", str)
    altitude = get_validated_input("Altitude (m): ", int, 0, 4000)
    variety = get_validated_input("Variety: ", str)

    # Process method choice (1–5)
    choice_map = {
        "1": "Natural",
        "2": "Washed",
        "3": "Honey",
        "4": "Wet-Hulled",
        "5": "Other",
    }
    print("Process Method:")
    for k, v in choice_map.items():
        print(f"{k}. {v}")
    process_choice = input("Choose (1–5): ").strip()
    process_method = choice_map.get(process_choice, None)

    purchase_date = get_validated_date("Purchase Date (MM/DD/YYYY, MM/DD/YY, or YYYY-MM-DD): ")

    new_row = {
        "id": next_id,
        "supplier": supplier,
        "country": country,
        "region": region,
        "altitude_meters": altitude,
        "variety": variety,
        "process_method": process_method,
        "purchase_date": purchase_date.strftime("%Y-%m-%d") if purchase_date else ""
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    print("✅ Coffee added to inventory.\n")
    return df

def remove_entry(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        print("\n⚠️ Inventory is empty.\n")
        return df
    list_inventory(df)
    choice = input("Enter ID to remove (or press Enter to cancel): ").strip()
    if choice and choice.isdigit():
        choice_id = int(choice)
        if choice_id in df["id"].values:
            df = df[df["id"] != choice_id]
            print(f"🗑️ Removed coffee with ID {choice_id}.\n")
        else:
            print("⚠️ Invalid ID.\n")
    return df

def edit_coffee_inventory():
    df = load_inventory()
    while True:
        print("Coffee Inventory Menu:")
        print("1. List Coffees")
        print("2. Add Coffee")
        print("3. Remove Coffee")
        print("4. Back to Main Menu")
        choice = input("Select an option: ").strip()

        if choice == "1":
            list_inventory(df)
        elif choice == "2":
            df = add_entry(df)
            save_inventory(df)
        elif choice == "3":
            df = remove_entry(df)
            save_inventory(df)
        elif choice == "4":
            break
        else:
            print("Invalid choice, try again.\n")
