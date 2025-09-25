from scripts.run_input_menu_session import run_input_menu_session
from scripts.utilities.capture_roast_session import capture_roast_session
from scripts.run_model_session import run_model_session
from scripts.ml_builder import main as train_models
from scripts.utilities.plotly_launcher import launch_plotly
from colorama import init
init(autoreset=True)


def main():
    while True:
        print("1. Add Roast Data")
        print("2. Run Predictions on Given Data")
        print("3. Rebuild Model with Roast Data")
        print("4. Plot Roast Data (Plotly on Default Browser)")
        print(r"(Editing bad data will have to be done on data\roast_data.jsonl)")
        print("5. Exit")

        choice = input("Select an option: ")

        if choice == "1":
            session_data = run_input_menu_session()
            capture_roast_session(session_data)
        elif choice == "2":
            run_model_session()
        elif choice == "3":
            train_models()
        elif choice == "4":
            launch_plotly()
        elif choice == "5":
            break
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()
