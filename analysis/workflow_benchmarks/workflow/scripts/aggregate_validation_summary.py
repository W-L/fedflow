import argparse
import re
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


METRICS_PATH_PATTERN = re.compile(r"nclients_(\d+)/size_(\d+)/rep_(\d+)/fedflow_metrics\.json$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def parse_triplet_from_metrics_path(path: Path) -> tuple[int, int, int]:
    normalized = str(path).replace("\\", "/")
    match = METRICS_PATH_PATTERN.search(normalized)
    if match is None:
        print(
            "WARNING: metrics path does not match expected pattern "
            f"nclients_<n>/size_<s>/rep_<r>/fedflow_metrics.json: {path}"
        )
        return -1, -1, -1
    nclients, size, rep = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return nclients, size, rep




def validate_run_dir(run_dir: Path, expected_zips: int) -> int:
    if not run_dir.exists():
        print(f"WARNING: run directory does not exist: {run_dir}")
        return 0

    zip_files = sorted(path for path in run_dir.glob("*.zip") if path.is_file())
    if len(zip_files) != expected_zips:
        print(
            f"WARNING: expected {expected_zips} zip files in {run_dir}, found {len(zip_files)}"
        )

    parsed_float_count = 0
    for zip_path in zip_files:
        number = None
        try:
            with ZipFile(zip_path) as archive:
                for name in archive.namelist():
                    if name.endswith("result.txt"):   
                        with archive.open(name, "r") as handle:
                            text = handle.read().decode("utf-8", errors="replace")
                            number = float(text.strip())

        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: failed to read zip {zip_path}: {exc}")
            continue

        
        if number is None:
            print(f"WARNING: no float found in {zip_path}")
            continue

        parsed_float_count += 1
    
    # additionally check for result.txt files in the run_dir itself
    for result_path in run_dir.glob("**/result.txt"):
        number = None
        try:
            with result_path.open("r", encoding="utf-8") as handle:
                text = handle.read()
                number = float(text.strip())
                if number is not None:
                    parsed_float_count += 1
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: failed to read result file {result_path}: {exc}")
            continue

    return parsed_float_count


def main() -> None:
    args = parse_args()

    rows = []
    for metrics_path in args.metrics:
        nclients, size, rep = parse_triplet_from_metrics_path(metrics_path)
        
        run_dir = metrics_path.parent
        float_count = validate_run_dir(
            run_dir=run_dir,
            expected_zips=nclients,
        )

        if float_count == 0:
            print(
                f"WARNING: no valid floats found for nclient={nclients}, size={size}, rep={rep}"
            )
            rows.append((nclients, size, rep, ""))
        else:
            rows.append((nclients, size, rep, float_count))

    df = pd.DataFrame(rows, columns=["nclient", "size", "rep", "n_floats"])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, sep="\t", index=False)


if __name__ == "__main__":
    main()
