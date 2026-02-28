import json, os, glob
def repair():
    paths = ["executive_manifests/*.json", "singularity_prime/governance/manifests/*.json", "agi1_autonomous_os/executives/*.json"]
    report = {"changed": [], "skipped": []}
    for pattern in paths:
        for path in glob.glob(pattern):
            try:
                with open(path, 'r') as f: data = json.load(f)
                updated = False
                if data.get("lifecycle_state") in ["STABLE", "ACTIVE", "active"]:
                    data["lifecycle_state"] = "UNDER_CONSTRUCTION"; updated = True
                if data.get("build_status") in ["STABLE", "ACTIVE", "active"]:
                    data["build_status"] = "UNDER_CONSTRUCTION"; updated = True
                if updated:
                    with open(path, 'w') as f: json.dump(data, f, indent=2)
                    report["changed"].append(path)
            except Exception as e: report["skipped"].append({"path": path, "error": str(e)})
    os.makedirs("agi1/reports", exist_ok=True)
    with open("agi1/reports/manifest_repair_report.json", "w") as f: json.dump(report, f, indent=2)
    print("✅ Manifest Repair Report Generated.")
repair()
