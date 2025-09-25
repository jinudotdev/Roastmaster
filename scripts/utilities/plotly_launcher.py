import pandas as pd
import plotly.express as px
import plotly.io as pio

pio.renderers.default = "browser"

def launch_plotly():
    df = pd.read_json("data/roast_data.jsonl", lines=True)

    # Flatten nested dicts
    session_df = pd.json_normalize(df["session_data"].tolist())
    features_df = pd.json_normalize(df["features"].tolist())
    df = pd.concat([session_df, features_df], axis=1).reset_index().rename(columns={"index": "roast_id"})

    stage_rows = []
    for idx, row in df.iterrows():
        # Add turning point as stage_num = 0.5
        if pd.notna(row.get("turning_point_temp")):
            stage_rows.append({
                "roast_id": idx,
                "supplier_name": row.get("supplier_name"),
                "origin_country": row.get("origin_country"),
                "roast_date": str(row.get("roast_date")).split(" ")[0],
                "stage": "turning_point",
                "stage_num": 0.5,
                "time_min": row.get("turning_point_time", 0) / 60.0,
                "bean_temp": row.get("turning_point_temp"),
                "burner_pct": None
            })

        # Add the logged stages
        if isinstance(row.get("stages"), list):
            for s in row["stages"]:
                stage_rows.append({
                    "roast_id": idx,
                    "supplier_name": row.get("supplier_name"),
                    "origin_country": row.get("origin_country"),
                    "roast_date": str(row.get("roast_date")).split(" ")[0],
                    "stage": s.get("stage"),
                    "stage_num": s.get("stage"),  # numeric stage index
                    "time_min": s.get("time_in_secs", 0) / 60.0,
                    "bean_temp": s.get("bean_temp"),
                    "burner_pct": s.get("burner_pct")
                })

    stage_df = pd.DataFrame(stage_rows)

    # Build custom label for legend
    stage_df["roast_label"] = (
        stage_df["supplier_name"].fillna("Unknown") + " • " +
        stage_df["origin_country"].fillna("Unknown") + " • " +
        stage_df["roast_date"].fillna("")
    )

    # Plot: bean temp vs time, one line per roast
    fig = px.line(
        stage_df.sort_values(["roast_id", "time_min"]),
        x="time_min",
        y="bean_temp",
        color="roast_label",
        markers=True,
        hover_data=["stage", "burner_pct"]
    )

    fig.update_layout(
        title="Roast Curves (with Turning Point)",
        xaxis_title="Elapsed Time (minutes)",
        yaxis_title="Bean Temp (°F)"
    )
    fig.update_xaxes(range=[0, 15])
    fig.update_yaxes(range=[200, 475])

    fig.show()
