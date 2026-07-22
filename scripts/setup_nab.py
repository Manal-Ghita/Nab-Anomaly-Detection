"""
Sets up the external NAB repo for this project: copies the custom Isolation
Forest detector into it, patches run.py to register it, patches the known
pandas-compatibility bug in labeler.py, and generates a restricted labels
file for quick single-file testing.

Usage (from the project root, assuming NAB/ is cloned as a sibling folder):
    python scripts/setup_nab.py --nab-path ../NAB
"""
import argparse
import json
import shutil
from pathlib import Path

DETECTOR_SOURCE = Path(__file__).parent.parent / "nab_integration" / "isolation_forest_detector.py"

RUN_PY_IMPORT_MARKER = 'if "isolationForest" in args.detectors:'
RUN_PY_IMPORT_BLOCK = (
    '  if "isolationForest" in args.detectors:\n'
    '        from nab.detectors.isolation_forest.isolation_forest_detector import (\n'
    '            IsolationForestDetector)\n'
)

LABELER_OLD_LINE = 'labels["label"].values[indices.values] = 1'
LABELER_NEW_LINE = 'labels.loc[indices, "label"] = 1'


def setup_detector(nab_path: Path):
    detector_dir = nab_path / "nab" / "detectors" / "isolation_forest"
    detector_dir.mkdir(parents=True, exist_ok=True)
    (detector_dir / "__init__.py").touch(exist_ok=True)
    shutil.copy(DETECTOR_SOURCE, detector_dir / "isolation_forest_detector.py")
    print(f"Copied detector to {detector_dir}")


def patch_run_py(nab_path: Path):
    run_py = nab_path / "run.py"
    content = run_py.read_text()
    if RUN_PY_IMPORT_MARKER in content:
        print("run.py already patched, skipping.")
        return
    content = content.replace(
        '  if args.skipConfirmation or checkInputs(args):',
        RUN_PY_IMPORT_BLOCK + '\n  if args.skipConfirmation or checkInputs(args):'
    )
    run_py.write_text(content)
    print("Patched run.py")


def patch_labeler(nab_path: Path):
    labeler_py = nab_path / "nab" / "labeler.py"
    content = labeler_py.read_text()
    if LABELER_OLD_LINE not in content:
        print("labeler.py already patched (or line not found), skipping.")
        return
    content = content.replace(LABELER_OLD_LINE, LABELER_NEW_LINE)
    labeler_py.write_text(content)
    print("Patched labeler.py (pandas read-only fix)")


def generate_test_windows(nab_path: Path, filename: str):
    windows_path = nab_path / "labels" / "combined_windows.json"
    with open(windows_path) as f:
        all_windows = json.load(f)

    key = f"realAWSCloudwatch/{filename}"
    subset = {key: all_windows[key]}

    out_path = nab_path / "labels" / "combined_windows_test.json"
    with open(out_path, "w") as f:
        json.dump(subset, f, indent=4)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nab-path", type=str, required=True,
                         help="Path to the cloned NAB repo (e.g. ../NAB)")
    parser.add_argument("--test-file", type=str,
                         default="ec2_cpu_utilization_825cc2.csv",
                         help="File to generate the restricted test labels for")
    args = parser.parse_args()

    nab_path = Path(args.nab_path).resolve()
    assert nab_path.exists(), f"NAB path not found: {nab_path}"

    setup_detector(nab_path)
    patch_run_py(nab_path)
    patch_labeler(nab_path)
    generate_test_windows(nab_path, args.test_file)

    print("\nSetup complete.")