from datetime import date


def score(results):
    total = len(results) * 2
    earned = sum(2 if r["result"] == "PASS"
                 else 1 if r["result"] == "UNKNOWN"
                 else 0
                 for r in results)
    return round((earned / total) * 100) if total > 0 else 0


def render(entity, since, results):
    s = score(results)
    print(f"\n{'='*60}")
    print(f"  {entity}")
    print(f"  Assert report — {date.today()}")
    print(f"  Monitoring since: {since}")
    print(f"  Score: {s}/100")
    print(f"{'='*60}\n")

    for r in results:
        icon = "✅" if r["result"] == "PASS" else \
               "❌" if r["result"] == "FAIL" else "⚠️ "
        print(f"{icon}  {r['id']}")
        print(f"    claim:    {r['claim']}")
        print(f"    result:   {r['result']}")
        print(f"    evidence: {r['evidence']}")
        print()

    failing = [r for r in results if r["result"] == "FAIL"]
    if failing:
        print(f"{'='*60}")
        print(f"  {len(failing)} failing assert(s) require attention")
        for r in failing:
            print(f"  → {r['id']}: {r['claim']}")
    print(f"{'='*60}\n")
