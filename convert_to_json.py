import os
import json
import csv


AGENTS = {
    "admissions": {
        "txt_files": [
            "data/admissions/2025_Cut_off.txt",
            "data/admissions/BE_or_B.Tech_Eligibility.txt",
            "data/admissions/COE informations.txt",
            "data/admissions/courses offered.txt",
            "data/admissions/FN students eligibilty.txt",
            "data/admissions/Lateral_entry_eligibility.txt",
            "data/admissions/ME Eligibility.txt",
            "data/admissions/Over seas citizens of india (OCI) students eligibility.txt",
            "data/admissions/NRI students eligibility.txt",
            "data/admissions/Sat_admissions.txt"
        ],
        "csv_files": [
            "data/admissions/lateral entry eligibility.csv",
            "data/admissions/TNEA 2025 Cut Off.csv"
        ],
        "json_files": [
            "data/admissions/All Course Syllabus.json",
        ],
        "output_file": "output/admissions_knowledge.json"
    },

    "placements": {
        "txt_files": [
            "data/placements/Foreign Language Training.txt",
            "data/placements/Internships.txt",
            "data/placements/Placement Summary.txt",
            "data/placements/Recruiting Companies.txt",
            "data/placements/Training Methods.txt",
            "data/placements/Context_Placement_2026_Highlights_Till_Dec_2025.txt",
            "data/placements/Context_Placement_Statistics_2023_24.txt",
            "data/placements/Context_Placement_Statistics_2024_25.txt",
            "data/placements/Context_Placement_Summary_2023_24.txt",
            "data/placements/Context_Placement_Summary_2024_25.txt",
        ],
        "csv_files": [
            "data/placements/Placement_Statistics_2023_24.csv",
            "data/placements/Placement_Statistics_2024_25.csv",
            "data/placements/Placement_2026_Highlights_Till_Dec_2025.csv",
            "data/placements/Placement_Summary_2024_25.csv",
            "data/placements/Placement_Summary_2023_24.csv",
        ],
        "json_files": [],
        "output_file": "output/placements_knowledge.json"
    },

    "Carrer_guidance": {
        "txt_files": [
            "data/Carrer guidance/career_paths.txt",
            "data/Carrer guidance/higher_studies.txt",
            "data/Carrer guidance/industry_trends.txt",
            "data/Carrer guidance/recruiting_companies.txt",
            "data/Carrer guidance/skills_required.txt",
        ],
        "csv_files": [],
        "json_files": [],
        "output_file": "output/Carrer_guidance.json"
    }
}

# Functions

def read_txt_file(filepath):
    """Read a .txt file and return as a dict with filename as key."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        topic = os.path.splitext(os.path.basename(filepath))[0]  # filename without extension
        print(f"  ✅ Loaded TXT: {filepath}")
        return {"topic": topic, "content": content}
    except FileNotFoundError:
        print(f"  ⚠️  Skipped (not found): {filepath}")
        return None


def read_csv_file(filepath):
    try:
        rows = []
        with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as f:
            content = f.read().replace("\x00", "")  # ← removes NUL characters
            reader = csv.DictReader(content.splitlines())
            for row in reader:
                clean_row = {(k.strip() if k is not None else ""): (v.strip() if v is not None else "") for k, v in row.items() if k is not None}
                rows.append(clean_row)
        topic = os.path.splitext(os.path.basename(filepath))[0]
        print(f"  ✅ Loaded CSV: {filepath}")
        return {"topic": topic, "data": rows}
    except FileNotFoundError:
        print(f"  ⚠️  Skipped (not found): {filepath}")
        return None


def read_json_file(filepath):
    """Read a .json file and return its contents."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)
        topic = os.path.splitext(os.path.basename(filepath))[0]
        print(f"  ✅ Loaded JSON: {filepath}")
        return {"topic": topic, "data": content}
    except FileNotFoundError:
        print(f"  ⚠️  Skipped (not found): {filepath}")
        return None


def combine_agent_data(agent_name, config):
    """Combine all TXT, CSV, and JSON files for one agent into a single dict."""
    print(f"\n📦 Processing agent: {agent_name.upper()}")

    combined = {
        "agent": agent_name,
        "text_data": [],
        "table_data": [],
        "structured_data": []
    }

    # Load TXT files
    for filepath in config["txt_files"]:
        result = read_txt_file(filepath)
        if result:
            combined["text_data"].append(result)

    # Load CSV files
    for filepath in config["csv_files"]:
        result = read_csv_file(filepath)
        if result:
            combined["table_data"].append(result)

    # Load JSON files
    for filepath in config["json_files"]:
        result = read_json_file(filepath)
        if result:
            combined["structured_data"].append(result)

    return combined


def save_json(data, output_path):
    """Save the combined data as a formatted JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  💾 Saved to: {output_path}")


# ============================================================
# MAIN — Run the conversion for all agents
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  CIT Knowledge Base Builder")
    print("  Converting CSV + TXT + JSON → Single JSON per Agent")
    print("=" * 50)

    for agent_name, config in AGENTS.items():
        combined_data = combine_agent_data(agent_name, config)
        save_json(combined_data, config["output_file"])

    print("\n✅ All done! Check the 'output/' folder for your JSON files.")
    print("\nOutput files:")
    for agent_name, config in AGENTS.items():
        print(f"  → {config['output_file']}")