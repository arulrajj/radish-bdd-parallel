import os
import re
import json

FEATURE_DIR = "features"

def parse_feature_file(file_path):
    scenarios = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match blocks of Gherkin scenarios
    matches = re.finditer(
        r"((?:@\w+\s*)*)\s*(Scenario(?: Outline)?:\s*.*?)(?=^\s*@|^\s*Scenario|\Z)",
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    for match in matches:
        tags_block = match.group(1)
        scenario_block = match.group(2)

        # Extract scenario name
        name_match = re.search(r"Scenario(?: Outline)?:\s*(.*)", scenario_block)
        name = name_match.group(1).strip()

        # Extract tags
        tags = [t.strip("@") for t in tags_block.split() if t.startswith("@")]

        scenarios.append({
            "feature_file": file_path,
            "scenario_name": name,
            "scenario_text": scenario_block,
            "tags": tags
        })

    return scenarios


def scan_all_features():
    all_scenarios = []

    for root, dirs, files in os.walk(FEATURE_DIR):
        for f in files:
            if f.endswith(".feature"):
                feature_path = os.path.join(root, f)
                all_scenarios.extend(parse_feature_file(feature_path))

    with open("scenarios.json", "w", encoding="utf-8") as f:
        json.dump(all_scenarios, f, indent=2)

    print(f"Extracted {len(all_scenarios)} scenarios into scenarios.json")


if __name__ == "__main__":
    scan_all_features()
