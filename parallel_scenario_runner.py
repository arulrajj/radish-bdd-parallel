import json
import os
import shutil
import subprocess
from multiprocessing import Pool, cpu_count
from extract_scenarios import extract_scenario_from_feature

SCENARIOS_FILE = "scenarios.json"
TAG = "Parallel_test"
TEMP_DIR = "temp_parallel_features"

# ALL BASE DIRS HERE
BASE_DIRS = [
    "-b", "PageOperations",
    "-b", "Util",
    "-b", "StepDefn"
]

def load_scenarios():
    with open(SCENARIOS_FILE) as f:
        data = json.load(f)

    selected = []

    for feature in data["features"]:
        feature_path = feature["filename"]
        for scenario in feature["scenarios"]:
            if TAG in scenario.get("tags", []):
                selected.append({
                    "feature": feature_path,
                    "name": scenario["name"]
                })

    return selected


def prepare_temp_files(selected):
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    temp_files = []

    for idx, sc in enumerate(selected, start=1):
        scenario_text = extract_scenario_from_feature(sc["feature"], sc["name"])

        temp_file = f"{TEMP_DIR}/scenario_{idx:03}.feature"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(f"Feature: Temp Scenario {idx}\n\n")
            f.write(scenario_text)

        temp_files.append(temp_file)

    return temp_files


def run_scenario_file(feature_file):
    print(f"🚀 Running {feature_file}")

    cmd = ["radish", feature_file] + BASE_DIRS

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    scenarios = load_scenarios()
    print(f"Found {len(scenarios)} scenarios with @{TAG}")

    temp_files = prepare_temp_files(scenarios)

    pool_size = min(cpu_count(), len(temp_files))

    with Pool(pool_size) as p:
        results = p.map(run_scenario_file, temp_files)

    if any(code != 0 for code in results):
        print("❌ Some parallel scenarios failed")
        exit(1)

    print("✅ All parallel scenarios passed")
    shutil.rmtree(TEMP_DIR)
    exit(0)
