THIS MAY BE DEPRECATED


Roastmaster — Local Coffee Roast Tracking & ML Prediction System
=================================================================

Roastmaster is a fully offline coffee roasting assistant that:

• Tracks coffee inventory  
• Records roast sessions  
• Trains “Scout” (small) and “Core” (large) ML models  
• Predicts roast curves and roast metadata  
• Provides CLI and GUI (PySide6) interfaces  

All data is stored locally in CSV form, and models are rebuilt on demand.

----------------------------------------------------------------------
Directory Structure
----------------------------------------------------------------------

├── main.py                         # CLI entrypoint
├── gui.py                          # GUI entrypoint (PySide6)
│
├── data/
│   ├── roast_data.csv              # Master roast log (MASTER_ORDER schema)
│   └── coffee_inventory.csv        # Bean inventory
|
├── gui/                            # PySide6 GUI application
│   ├── gui_capture_roast_session.py 
│   ├── gui_curve_plot.py 
│   ├── gui_edit_coffee_inventory.py 
│   ├── gui_inference_core_input_session.py 
│   ├── gui_inference_scout_input_session.py 
│   ├── gui_main_window.py gui/gui_paths.py 
│   ├── gui_print_core_report.py 
│   └── gui_print_scout_report.py
│
├── models/
│   ├── core/                       # Saved large Core model + metadata
│   └── scout/                      # Saved small Scout model + metadata
│
├── scripts_main/                   # All CLI flows
│   ├── capture_roast_session.py
│   ├── edit_coffee_inventory.py
│   ├── roast_data_input_session.py
│
│   ├── inference_scout_input_session.py
│   ├── inference_core_input_session.py
│
│   ├── infer_scout.py
│   ├── infer_core.py
│
│   ├── print_scout_report.py
│   ├── print_core_report.py
│
│   ├── train_scout.py
│   ├── train_core.py
│   ├── train_core_config.py
│   └── shared utilities
│
├── scripts_utility/
│   ├── master_order.py             # Canonical CSV field ordering
│   ├── model_utils.py              # Shared ML helpers
│   ├── paths.py                    # Project paths
│   ├── preprocess_scout.py         # Feature engineering for Scout model
│   ├── preprocess_core.py          # Feature engineering for Core model
│   └── shared helpers
