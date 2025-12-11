import re

def extract_scenario_from_feature(feature_file, scenario_name):
    with open(feature_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to match the full scenario block
    # Handles Scenario and Scenario Outline
    pattern = rf"(@.*\n)*\s*Scenario(?: Outline)?:\s*{re.escape(scenario_name)}[\s\S]*?(?=^\s*@|\s*Scenario|\Z)"
    match = re.search(pattern, content, re.MULTILINE)

    if not match:
        raise ValueError(f"Scenario text not found: {scenario_name}")

    return match.group(0)
