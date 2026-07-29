#%%
import json
from pathlib import Path
import re

import pandas as pd 


# glob metrics from benchmark
metrics_files = sorted(Path("../results").glob("nclients_*/size_*/rep_*/fedflow_metrics.json"))
print(len(metrics_files))



#%%
# Parse metrics payloads into run-level and phase-level tables.
run_rows = []
phase_rows = []
path_pattern = re.compile(r"nclients_(\d+)/size_(\d+)/rep_(\d+)")

for metrics_path in metrics_files:
    print(metrics_path)
    m = path_pattern.search(str(metrics_path))
    if m is None:
        continue

    n_clients = int(m.group(1))
    data_size = int(m.group(2))
    rep = int(m.group(3))

    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    resources = payload.get("resources", {})
    
    run_rows.append(
        {
            "nclients": n_clients,
            "data_size": data_size,
            "rep": rep,
            "status": payload.get("status", "unknown"),
            "wall_clock_seconds": resources.get("wall_clock_seconds"),
            "process_cpu_seconds": resources.get("process_cpu_seconds"),
            "peak_rss_kib": resources.get("peak_rss_kib"),
        }
    )

    for phase in payload.get("phases", []):
        phase_rows.append(
            {
                "nclients": n_clients,
                "data_size": data_size,
                "rep": rep,
                "phase": phase.get("name"),
                "duration_seconds": phase.get("duration_seconds"),
            }
        )


#%%

df = pd.DataFrame(run_rows)
phase_df = pd.DataFrame(phase_rows)

# transform variables
df['peak_rss_mib'] = df['peak_rss_kib'] / 1024


df.to_csv("metrics_long.csv", index=False)
phase_df.to_csv("metrics_phase_long.csv", index=False)


# %%
