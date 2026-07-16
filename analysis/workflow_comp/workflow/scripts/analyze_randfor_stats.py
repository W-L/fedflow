#%%
import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from scipy import stats

# label for the pooled federated category
FED_AGGREGATE_LABEL = "federated (aggregate)"



def extract_repeat(path: str) -> str:
    match = re.search(r"/(?:fed|cent)/(\d{3})/", path)
    if not match:
        raise ValueError(f"Could not parse repeat from path: {path}")
    return match.group(1)


def read_cent(cent_test_path: str, cent_proba_path: str) -> pd.DataFrame:
    df_test = pd.read_csv(cent_test_path, sep="\t")
    df_proba = pd.read_csv(cent_proba_path)
    return pd.concat([df_test, df_proba], axis=1)


def read_fed(fed_combined_path: str) -> pd.DataFrame:
    return pd.read_csv(fed_combined_path)


def compute_roc_curve(y_true: np.ndarray, y_score: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=float)

    positives = (y_true == 1).sum()
    negatives = (y_true == 0).sum()
    if positives == 0 or negatives == 0:
        raise ValueError("Both classes must be present to compute ROC.")

    order = np.argsort(-y_score, kind="mergesort")
    y_true_sorted = y_true[order]
    y_score_sorted = y_score[order]

    distinct = np.where(np.diff(y_score_sorted))[0]
    threshold_idxs = np.r_[distinct, y_true_sorted.size - 1]

    tps = np.cumsum(y_true_sorted)[threshold_idxs]
    fps = 1 + threshold_idxs - tps
    tps = np.r_[0, tps]
    fps = np.r_[0, fps]

    tpr = tps / positives
    fpr = fps / negatives
    return fpr, tpr


def trapz_auc(fpr: np.ndarray, tpr: np.ndarray) -> float:
    return float(np.sum(np.diff(fpr) * (tpr[:-1] + tpr[1:]) / 2.0))


def aggregate_roc(curves: list[tuple[np.ndarray, np.ndarray]], client: str) -> pd.DataFrame:
    grid = np.linspace(0.0, 1.0, 201)
    interp_tprs = []
    for fpr, tpr in curves:
        interp = np.interp(grid, fpr, tpr)
        interp[0] = 0.0
        interp[-1] = 1.0
        interp_tprs.append(interp)

    tpr_stack = np.vstack(interp_tprs)
    mean_tpr = tpr_stack.mean(axis=0)
    std_tpr = tpr_stack.std(axis=0, ddof=1) if tpr_stack.shape[0] > 1 else np.zeros_like(mean_tpr)

    return pd.DataFrame({
        "client": client,
        "fpr": grid,
        "mean_tpr": mean_tpr,
        "std_tpr": std_tpr,
        "lower_tpr": np.clip(mean_tpr - std_tpr, 0.0, 1.0),
        "upper_tpr": np.clip(mean_tpr + std_tpr, 0.0, 1.0),
    })


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze repeated random-forest runs")
    parser.add_argument("--cent-prefix", required=True)
    parser.add_argument("--fed-prefix", required=True)
    parser.add_argument("--output-prefix", required=True)
    return parser.parse_args()


#%%

args = get_args()
cent_prefix = Path(args.cent_prefix)
fed_prefix = Path(args.fed_prefix)
output_prefix = Path(args.output_prefix)

# cent_prefix = Path("../../results/biosphere/random-forest/cent")
# fed_prefix = Path("../../results/biosphere/random-forest/fed")
# output_prefix = Path("../../results/biosphere/random-forest/stats")


cent_proba_files = sorted(cent_prefix.rglob("proba.csv"))
cent_test_files  = sorted(cent_prefix.rglob("test.csv"))
fed_files        = sorted(fed_prefix.rglob("combined_randfor.csv"))

cent_proba_by_rep = {extract_repeat(str(p)): str(p) for p in cent_proba_files}
cent_test_by_rep  = {extract_repeat(str(p)): str(p) for p in cent_test_files}
fed_by_rep        = {extract_repeat(str(p)): str(p) for p in fed_files}
repeats = sorted(set(cent_proba_by_rep) & set(cent_test_by_rep) & set(fed_by_rep))
print(len(repeats))

#%%


auc_rows:       list[dict] = []
paired_rows:    list[dict] = []
proba_parts:    list[pd.DataFrame] = []
ppscatter_parts: list[pd.DataFrame] = []
curves_by_client = defaultdict(list)

for rep in repeats:
    cent_df = read_cent(cent_test_by_rep[rep], cent_proba_by_rep[rep])
    fed_df  = read_fed(fed_by_rep[rep])

    # centralized 
    y_true_cent = cent_df["y_true"].to_numpy()
    prob_cent   = cent_df["prob_1"].to_numpy()
    fpr_c, tpr_c = compute_roc_curve(y_true_cent, prob_cent)
    auc_cent = trapz_auc(fpr_c, tpr_c)
    curves_by_client["centralized"].append((fpr_c, tpr_c))
    auc_rows.append({"repeat": rep, "client": "centralized", "auc": auc_cent})

    cent_ann = cent_df[["y_true", "prob_1"]].copy()
    cent_ann["repeat"] = rep
    cent_ann["client"] = "centralized"
    proba_parts.append(cent_ann)

    # federated aggregate (all cohorts pooled)
    y_true_agg = fed_df["y_true"].to_numpy()
    prob_agg   = fed_df["prob_1"].to_numpy()
    fpr_a, tpr_a = compute_roc_curve(y_true_agg, prob_agg)
    auc_agg = trapz_auc(fpr_a, tpr_a)
    curves_by_client[FED_AGGREGATE_LABEL].append((fpr_a, tpr_a))
    auc_rows.append({"repeat": rep, "client": FED_AGGREGATE_LABEL, "auc": auc_agg})
    paired_rows.append({
        "repeat": rep,
        "auc_centralized": auc_cent,
        "auc_federated":   auc_agg,
        "delta_auc":       auc_agg - auc_cent,
    })

    agg_ann = fed_df[["y_true", "prob_1"]].copy()
    agg_ann["repeat"] = rep
    agg_ann["client"] = FED_AGGREGATE_LABEL
    proba_parts.append(agg_ann)

    # per federated cohort
    for cohort in sorted(fed_df["client"].unique()):
        sub = fed_df[fed_df["client"] == cohort]
        y_true_co = sub["y_true"].to_numpy()
        prob_co   = sub["prob_1"].to_numpy()
        fpr_co, tpr_co = compute_roc_curve(y_true_co, prob_co)
        auc_co = trapz_auc(fpr_co, tpr_co)
        curves_by_client[cohort].append((fpr_co, tpr_co))
        auc_rows.append({"repeat": rep, "client": cohort, "auc": auc_co})

        sub_ann = sub[["y_true", "prob_1"]].copy()
        sub_ann["repeat"] = rep
        sub_ann["client"] = cohort
        proba_parts.append(sub_ann)

    # P-P scatter: pair cent vs fed by row position (same split, same order)
    scatter = fed_df[["y_true", "prob_1", "client"]].copy()
    scatter = scatter.rename(columns={"prob_1": "prob_1_fed"})
    scatter["prob_1_cent"] = prob_cent   # positional alignment within the split
    scatter["repeat"] = rep
    ppscatter_parts.append(scatter)


#%%
# aggregate across repeats

auc_long_df   = pd.DataFrame(auc_rows)
proba_all_df  = pd.concat(proba_parts, ignore_index=True)
ppscatter_df  = pd.concat(ppscatter_parts, ignore_index=True)
paired_df     = pd.DataFrame(paired_rows).sort_values("repeat")

roc_agg_df = pd.concat(
    [aggregate_roc(curves, client) for client, curves in curves_by_client.items()],
    ignore_index=True,
)

# summary stats (aggregate fed vs centralized)
deltas    = paired_df["delta_auc"].to_numpy(dtype=float)
n         = deltas.size
mean_delta = float(np.mean(deltas))
std_delta  = float(np.std(deltas, ddof=1)) if n > 1 else float("nan")
se_delta   = std_delta / np.sqrt(n) if n > 1 else float("nan")
t_crit     = stats.t.ppf(0.975, df=n - 1)
ci_low     = mean_delta - t_crit * se_delta
ci_high    = mean_delta + t_crit * se_delta

summary_df = pd.DataFrame([{
    "n_repeats":     int(n),
    "mean_delta_auc": mean_delta,
    "sd_delta_auc":   std_delta,
    "se_delta_auc":   se_delta,
    "ci95_low":       ci_low,
    "ci95_high":      ci_high,
}])

fed_auc_values  = paired_df["auc_federated"].to_numpy(dtype=float)
cent_auc_values = paired_df["auc_centralized"].to_numpy(dtype=float)
wilcoxon_res = stats.wilcoxon(
    fed_auc_values,
    cent_auc_values,
    zero_method="wilcox",
    alternative="two-sided",
    method="auto",
)
wilcoxon_df = pd.DataFrame([{
    "test":      "wilcoxon_signed_rank",
    "statistic": cast(float, wilcoxon_res[0]),
    "p_value":   cast(float, wilcoxon_res[1]),
    "n_pairs":   int(n),
}])


#%%
# write output files
output_prefix.mkdir(parents=True, exist_ok=True)

auc_long_df.to_csv(output_prefix / "auc_long.csv",        index=False)
paired_df.to_csv(  output_prefix / "paired_auc.csv",      index=False)
summary_df.to_csv( output_prefix / "paired_summary.csv",  index=False)
wilcoxon_df.to_csv(output_prefix / "wilcoxon.csv",        index=False)
roc_agg_df.to_csv( output_prefix / "roc_aggregate.csv",   index=False)
proba_all_df.to_csv(output_prefix / "proba_all.csv",      index=False)
ppscatter_df.to_csv(output_prefix / "ppscatter.csv",      index=False)

# %%
