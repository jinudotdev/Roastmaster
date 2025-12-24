## What RoastMaster Does
RoastMaster is a coffee roasting tool built for an industrial-size Probat/Burns 540 lb roaster that works in a specific way. However, it can work for any roaster of similar operation given enough data (see below for specifics).

<br>

<div align="center">
  <img src="https://raw.githubusercontent.com/jinudotdev/jinudotdev.github.io/main/assets/images/2025-12-23-RoastmasterGUI.png" width="400" alt="Roastmaster">
  <p><em>This is the RoastMaster GUI</em></p>
</div>

<br>

## Why The Probat/Burns 23R Is Different
Unlike many roasters where the operator controls gas throughout the roast or automatically follows a continuous curve, this machine follows nine fixed stages. At each stage, you enter a target bean temperature and a fuel percentage, but you don’t control how long the roaster takes to get there. Time is affected by room temperature, humidity, bean condition, and other variables that change day to day.

## The Machine Learning Approach
Consistency matters, and relying only on experience makes it hard to account for all of those factors every time. RoastMaster was written to see if logged roast data and simple machine learning models could help make better estimates and improve repeatability. It uses a CatBoost model because it can learn effectively even when some categorical data is missing.

RoastMaster includes two models with different goals.

## Scout Model
Scout is a smaller model meant to work with limited data. It focuses on predicting roast behavior when roasting to specific temperatures and times, while adjusting for room and bean conditions. Scout is designed to become useful fairly quickly, even with a small number of logged roasts (however, the more sample data closer to the environment conditions that you have will determine how dependable that data would be)

## Core Model
Core is a larger model that uses more inputs and predicts more values. It will need a lot more data before it can be trusted across different roast profiles.

## Long‑Term Vision
The long‑term goal for Core is to move away from fixed targets and instead roast toward a desired taste profile, given enough roast and cupping data. Given a target flavor and current conditions (room temperature, humidity, bean age, etc.), Core is meant to return the exact numbers needed at each stage of the roast.

Ideally, hundreds of roast curves, along all sorts of room conditions and bean types, would make for a stellar model. Just like a real coffee roaster learning through experience, RoastMaster is doing the same thing, so think of it as a Trainee, Apprentice, then a Coworker that you can bounce ideas off of (Cupping, however, is still up to you 🙂)

## Installation
See HOWTOINSTALL.txt for setup instructions.

## Directory Structure

```text
├── main.py                         # CLI entrypoint
├── gui.py                          # GUI entrypoint (PySide6)
│
├── data/
│   ├── roast_data.csv              # Master roast log (MASTER_ORDER schema)
│   └── coffee_inventory.csv        # Bean inventory
│
├── gui/                            # PySide6 GUI application
│   ├── gui_capture_roast_session.py
│   ├── gui_curve_plot.py
│   ├── gui_edit_coffee_inventory.py
│   ├── gui_inference_core_input_session.py
│   ├── gui_inference_scout_input_session.py
│   ├── gui_main_window.py
│   ├── gui_paths.py
│   ├── gui_print_core_report.py
│   └── gui_print_scout_report.py
│
├── models/
│   ├── core/                       # Saved Core model + metadata
│   └── scout/                      # Saved Scout model + metadata
│
├── scripts_main/                   # All CLI flows
│   ├── capture_roast_session.py
│   ├── edit_coffee_inventory.py
│   ├── roast_data_input_session.py
│   ├── inference_scout_input_session.py
│   ├── inference_core_input_session.py
│   ├── infer_scout.py
│   ├── infer_core.py
│   ├── print_scout_report.py
│   ├── print_core_report.py
│   ├── train_scout.py
│   ├── train_core.py
│   └── train_core_config.py
│
├── scripts_utility/
│   ├── master_order.py             # Canonical CSV field ordering
│   ├── paths.py                    # Project paths
│   └── schema.py                   # Roast session schema
