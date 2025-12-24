RoastMaster
RoastMaster is a coffee‑roasting tool built for an industrial Probat/Burns 540 lb roaster that operates in a very specific way. It uses machine‑learning models to improve roast consistency and predict roast behavior under varying conditions.

Installation
See HOWTOINSTALL.txt for setup instructions.

What Makes This Roaster Different
Unlike many roasters where the operator adjusts gas throughout the roast or follows a continuous curve, this machine runs through nine fixed stages. At each stage you enter a target bean temperature and a fuel percentage, but not the time it takes to reach that target. The duration varies based on room temperature, humidity, bean condition, and other day‑to‑day factors.

Machine Learning Models
RoastMaster uses CatBoost models to learn from logged roast data and improve repeatability.

Scout Model — lightweight, works with limited data, predicts roast behavior for specific temperature/time targets.

Core Model — larger, uses more inputs, predicts more values, and requires more data before it can be trusted across profiles.

Long‑Term Vision
The Core model is intended to eventually roast toward a desired taste profile, given enough roast and cupping data.

Directory Structure

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
