from scripts.user_menu import menu_session, predict_mode
from scripts.utilities.storage import save_session
from scripts.run_model_session import run_model_session
from scripts.audit_data import audit_data
from scripts.ml_builder import main as train_models

def main():
    while True:
            print("\nMain Menu")
            print("1) Add Data")
            print("2) Run Model (use latest trained model)")
            print("3) Audit Data")
            print("4) Train Model (rebuild from roast logs)")
            print("5) Exit")

            choice = input("Select an option: ")

            if choice == "1":
                menu_session()
            elif choice == "2":
                run_model_session()
            elif choice == "3":
                audit_data()
            elif choice == "4":
                train_models()
            elif choice == "5":
                break
            else:
                print("Invalid choice, try again.")

if __name__ == "__main__":
    main()