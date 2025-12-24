from scripts_main.roast_data_input_session import roast_data_input_session
from scripts_main.capture_roast_session import capture_roast_session
from scripts_main.edit_coffee_inventory import edit_coffee_inventory
from scripts_main.inference_core_input_session import core_input_session
from scripts_main.inference_scout_input_session import scout_input_session
from scripts_main.print_core_report import print_core_report
from scripts_main.print_scout_report import print_scout_report
from scripts_main.train_core import main as train_core
from scripts_main.train_scout import main as train_scout
from scripts_main.infer_core import infer_core
from scripts_main.infer_scout import infer_scout
from colorama import init
init(autoreset=True)


def main():
    while True:
        print("1. Add Roast Data")
        print("2. Add/Remove Coffee from Inventory")
        print("3. Run Scout (Small) Prediction on Given Data")
        print("4. Rebuild Scout (Small) Model with Roast Data")
        print("5. Run Core (Big) Prediction on Given Data")
        print("6. Rebuild Core (Big) Model with Roast Data")
        print(r"(Core Model will require lots of data before accurate inference can be made.)")
        print(r"(Run both models until you are sure.)")
        print(r"(Editing bad data will have to be done on data\roast_data.csv)")
        print("7. Exit")

        choice = input("Select an option: ")

        if choice == "1":
            session_data = roast_data_input_session()
            capture_roast_session(session_data)
        elif choice == "2":
            edit_coffee_inventory()
        elif choice == "3":
            flat_inputs = scout_input_session()
            ml_filled_fields, confidence  = infer_scout(flat_inputs)
            print_scout_report(flat_inputs, confidence, ml_filled_fields)
        elif choice == "4":
            train_scout()
        elif choice == "5":
            flat_inputs = core_input_session()
            ml_filled_fields, confidence = infer_core(flat_inputs)
            print_core_report(flat_inputs, confidence, ml_filled_fields)
        elif choice == "6":
            train_core()
        elif choice == "7":
            break
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
