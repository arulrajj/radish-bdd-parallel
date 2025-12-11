import json
import os
import subprocess
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed


class ParallelScenarioRunner:
    def __init__(self, json_file, radish_base_dirs, threads=5):
        """
        :param json_file: Path to flattened scenario JSON
        :param radish_base_dirs: List of base dirs for radish execution
        :param threads: Number of parallel threads
        """
        self.json_file = json_file
        self.radish_base_dirs = radish_base_dirs
        self.threads = threads

        # Load scenarios from JSON file
        with open(json_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.scenarios = self.load_scenarios()

    # ----------------------------------------------------
    # LOAD SCENARIOS
    # ----------------------------------------------------
    def load_scenarios(self):
        """
        Your JSON structure is:
        [
          {
            "feature_file": "...",
            "scenario_name": "...",
            "scenario_text": "...",
            "tags": ["Parallel_test", ...]
          }
        ]
        """
        scenarios = []
        for item in self.data:
            scenarios.append({
                "feature_file": item.get("feature_file"),
                "scenario_name": item.get("scenario_name"),
                "scenario_text": item.get("scenario_text"),
                "tags": [t.lower() for t in item.get("tags", [])],
            })
        return scenarios

    # ----------------------------------------------------
    # FILTERING PARALLEL SCENARIOS
    # ----------------------------------------------------
    def is_parallel(self, scenario):
        return "parallel_test" in scenario["tags"]

    # ----------------------------------------------------
    # CREATE TEMPORARY FEATURE FILE
    # ----------------------------------------------------
    def generate_feature_file(self, scenario):
        """
        Creates a unique temporary directory and a single-scenario feature file
        """
        temp_dir = tempfile.mkdtemp(prefix="radish_parallel_")

        safe_name = scenario["scenario_name"].replace(" ", "_").replace("/", "_")
        feature_path = os.path.join(temp_dir, f"{safe_name}.feature")

        with open(feature_path, "w", encoding="utf-8") as f:
            f.write(f"Feature: {scenario['feature_file']}\n\n")
            f.write(scenario["scenario_text"])

        return feature_path, temp_dir

    # ----------------------------------------------------
    # RUN A SINGLE SCENARIO
    # ----------------------------------------------------
    def run_scenario(self, scenario):
        feature_path, temp_dir = self.generate_feature_file(scenario)

        # Build radish command
        cmd = ["radish", feature_path]
        for base in self.radish_base_dirs:
            cmd.extend(["--basedir", base])

        print(f"\n🚀 Running scenario: {scenario['scenario_name']}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = (
                f"==== SCENARIO: {scenario['scenario_name']} ====\n"
                f"{result.stdout}\n{result.stderr}\n"
            )
        except Exception as e:
            output = f"ERROR running scenario {scenario['scenario_name']}: {str(e)}"
        finally:
            # Cleanup temp directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

        return scenario["scenario_name"], output

    # ----------------------------------------------------
    # PARALLEL EXECUTION
    # ----------------------------------------------------
    def run_parallel(self):
        parallel_scenarios = [s for s in self.scenarios if self.is_parallel(s)]

        print(f"\n🔍 Found {len(parallel_scenarios)} scenarios with @Parallel_test")

        results = {}

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_map = {
                executor.submit(self.run_scenario, s): s
                for s in parallel_scenarios
            }

            for future in as_completed(future_map):
                name, output = future.result()
                results[name] = output
                print(f"✔ Completed: {name}")

        return results


# ----------------------------------------------------
# MAIN EXECUTION ENTRY
# ----------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Radish BDD Scenarios in Parallel")
    parser.add_argument("--json", required=True, help="Path to scenario JSON file")
    parser.add_argument("--threads", type=int, default=5, help="Number of parallel threads")
    parser.add_argument(
        "--basedirs",
        nargs="+",
        required=True,
        help="List of Radish --basedir directories"
    )

    args = parser.parse_args()

    runner = ParallelScenarioRunner(
        json_file=args.json,
        radish_base_dirs=args.basedirs,
        threads=args.threads
    )

    results = runner.run_parallel()

    # Write combined output to file
    with open("parallel_results.log", "w", encoding="utf-8") as f:
        for scenario_name, output in results.items():
            f.write(output + "\n")

    print("\n📄 Results saved to parallel_results.log\n")
    print("🎉 Parallel execution completed!\n")
