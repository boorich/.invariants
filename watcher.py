import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from fetchers.github import GithubFetcher
from report import render

load_dotenv()

FETCHER_MAP = {
    "github_activity": GithubFetcher,
}


def load_invariants(path=".invariants"):
    with open(path) as f:
        return yaml.safe_load(f)


def load_suite(suite_name):
    path = Path(f"suites/{suite_name}.yml")
    with open(path) as f:
        return yaml.safe_load(f)


def evaluate(assert_def, metrics):
    metric = assert_def["condition"]["metric"]
    operator = assert_def["condition"]["operator"]
    threshold = assert_def["condition"]["threshold"]
    value = metrics.get(metric)

    if value is None:
        return "UNKNOWN", "Metric not available", value

    ops = {
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        "==": lambda a, b: a == b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
    }

    passed = ops[operator](value, threshold)
    result = "PASS" if passed else "FAIL"
    evidence = assert_def.get("evidence_template", "{value}").format(value=value)
    return result, evidence, value


def main():
    inv_path = sys.argv[1] if len(sys.argv) > 1 else ".invariants"
    inv = load_invariants(inv_path)
    suite = load_suite(inv["suite"])

    # merge suite asserts + custom asserts
    all_asserts = suite["asserts"] + inv.get("custom_asserts", [])

    # collect metrics from each declared watcher
    metrics = {}
    for watcher_name in inv["watchers"]:
        FetcherClass = FETCHER_MAP.get(watcher_name)
        if not FetcherClass:
            print(f"Warning: no fetcher for watcher '{watcher_name}'")
            continue
        fetcher = FetcherClass(org=inv["org"])
        metrics.update(fetcher.collect(
            founding_team_handles=inv.get("founding_team_handles"),
            sample_size=inv.get("sample_size"),
        ))

    # evaluate all asserts
    results = []
    for assert_def in all_asserts:
        result, evidence, value = evaluate(assert_def, metrics)
        results.append({
            "id": assert_def["id"],
            "claim": assert_def["claim"],
            "result": result,
            "evidence": evidence,
            "value": value,
            "threshold": assert_def["condition"]["threshold"],
        })

    render(inv["entity"], inv["since"], results)


if __name__ == "__main__":
    main()
