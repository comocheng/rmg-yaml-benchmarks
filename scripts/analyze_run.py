#!/usr/bin/env python3

import argparse
import csv
import datetime
import json
import logging
import os
import pstats
import re
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze one RMG YAML benchmark run."
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--history-csv", default="results/benchmark_history.csv")
    parser.add_argument("--top-n", type=int, default=75)
    
    parser.add_argument("--allow-missing-profile",action="store_true",help="Write a partial report/CSV/JSON if RMG.profile is missing.",)
    return parser.parse_args()


def read_key_value_file(path):
    data = {}

    path = Path(path)
    if not path.exists():
        return data

    for line in path.read_text(errors="replace").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    return data


def find_profile_file(run_dir):
    run_dir = Path(run_dir)

    candidates = (
        list(run_dir.glob("*.profile"))
        + list(run_dir.glob("*.prof"))
        + list(run_dir.glob("RMG.profile"))
    )

    candidates = [
        p for p in candidates
        if p.is_file()
        and not str(p).endswith(".dot")
        and not str(p).endswith(".pdf")
        and not str(p).endswith(".ps2")
    ]

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def extract_number(path):
    nums = re.findall(r"\d+", path.name)
    if not nums:
        return -1
    return int(nums[-1])


def latest_file(folder, patterns):
    folder = Path(folder)
    if not folder.exists():
        return None

    files = []
    for pattern in patterns:
        files.extend(folder.glob(pattern))

    files = [p for p in files if p.is_file()]
    if not files:
        return None

    return sorted(files, key=lambda p: (extract_number(p), p.stat().st_mtime))[-1]


def find_latest_outputs(run_dir):
    run_dir = Path(run_dir)

    cantera_dir = run_dir / "cantera"
    chemkin_dir = run_dir / "chemkin"

    latest_yaml = latest_file(
        cantera_dir,
        ["*.yaml", "*.yml"],
    )

    latest_chemkin = latest_file(
        chemkin_dir,
        ["*.inp", "*chem*.txt", "*chem*.dat"],
    )

    species_dict = latest_file(
        chemkin_dir,
        ["species_dictionary.txt", "*species*dictionary*.txt"],
    )

    transport_file = latest_file(
        chemkin_dir,
        ["tran.dat", "transport.dat", "*tran*.dat", "*transport*.dat"],
    )

    return {
        "yaml_file": latest_yaml,
        "chemkin_file": latest_chemkin,
        "species_dictionary": species_dict,
        "transport_file": transport_file,
    }


def categorize_function(filename, function_name):
    text = f"{filename} {function_name}".lower()

    if "yaml" in text or "cantera" in text:
        return "yaml_writer"
    if "chemkin" in text:
        return "chemkin_writer"
    if "save_everything" in text or "save_output" in text or "output" in text:
        return "all_output"
    if "thermo" in text:
        return "thermo"
    if "kinetics" in text:
        return "kinetics"
    if "react" in text or "reaction" in text:
        return "reaction_generation"
    if "enlarge" in text:
        return "model_enlarge"
    if "database" in text or "family" in text or "library" in text:
        return "database"
    if "copy" in text or "deepcopy" in text:
        return "copying"
    if "html" in text or "render" in text:
        return "html_output"

    return "other"


def process_profile_stats(profile_path):
    stats = pstats.Stats(str(profile_path))
    stats.strip_dirs()

    total_time = stats.total_tt
    function_rows = []
    category_totals = {}

    for func, stat in stats.stats.items():
        filename, line_number, function_name = func
        primitive_calls, total_calls, self_time, cumulative_time, callers = stat

        category = categorize_function(filename, function_name)

        if category not in category_totals:
            category_totals[category] = {
                "self_time_s": 0.0,
                "cumulative_time_s": 0.0,
                "primitive_calls": 0,
                "total_calls": 0,
                "function_count": 0,
            }

        category_totals[category]["self_time_s"] += self_time
        category_totals[category]["cumulative_time_s"] += cumulative_time
        category_totals[category]["primitive_calls"] += primitive_calls
        category_totals[category]["total_calls"] += total_calls
        category_totals[category]["function_count"] += 1

        function_rows.append(
            {
                "filename": filename,
                "line_number": line_number,
                "function": function_name,
                "category": category,
                "primitive_calls": primitive_calls,
                "total_calls": total_calls,
                "self_time_s": self_time,
                "cumulative_time_s": cumulative_time,
                "self_percent": 100 * self_time / total_time if total_time else 0.0,
                "cumulative_percent": 100 * cumulative_time / total_time if total_time else 0.0,
            }
        )

    function_rows_by_cumulative = sorted(
        function_rows,
        key=lambda row: row["cumulative_time_s"],
        reverse=True,
    )

    function_rows_by_self = sorted(
        function_rows,
        key=lambda row: row["self_time_s"],
        reverse=True,
    )

    category_rows = []
    for category, values in category_totals.items():
        category_rows.append(
            {
                "category": category,
                **values,
                "self_percent": 100 * values["self_time_s"] / total_time if total_time else 0.0,
                "cumulative_percent": 100 * values["cumulative_time_s"] / total_time if total_time else 0.0,
            }
        )

    category_rows = sorted(
        category_rows,
        key=lambda row: row["cumulative_time_s"],
        reverse=True,
    )

    return {
        "total_time_s": total_time,
        "function_rows": function_rows,
        "function_rows_by_cumulative": function_rows_by_cumulative,
        "function_rows_by_self": function_rows_by_self,
        "category_rows": category_rows,
        "category_totals": category_totals,
    }


def make_profile_graph_pdf(stats_file, force_graph_generation=True):
    """
    Cluster-safe version of RMG's profile graph generation.

    It mirrors RMG's gprof2dot settings:
    - node_thres = 0.8
    - edge_thres = 0.1
    - color theme
    - total time and self time shown

    It writes:
    - RMG.profile.dot
    - RMG.profile.dot.pdf

    Unlike the original RMG helper, this uses dot -Tpdf directly instead
    of ps2 + ps2pdf, which is easier on SLURM/headless nodes.
    """

    stats_file = str(stats_file)

    if not force_graph_generation and not os.environ.get("DISPLAY"):
        logging.warning("No DISPLAY found. Skipping profile graph generation.")
        return {
            "dot_file": None,
            "pdf_file": None,
            "graph_status": "skipped_no_display",
        }

    try:
        from gprof2dot import (
            SAMPLES,
            TIME,
            TIME_RATIO,
            TOTAL_TIME,
            TOTAL_TIME_RATIO,
            DotWriter,
            PstatsParser,
            themes,
        )
    except ImportError:
        logging.warning("Could not import gprof2dot. Install with: pip install gprof2dot")
        return {
            "dot_file": None,
            "pdf_file": None,
            "graph_status": "failed_missing_gprof2dot",
        }

    class Options:
        pass

    options = Options()
    options.node_thres = 0.8
    options.edge_thres = 0.1
    options.strip = False
    options.show_samples = False
    options.root = ""
    options.leaf = ""
    options.wrap = True

    theme = themes["color"]
    theme.fontname = "ArialMT"

    parser = PstatsParser(stats_file)
    profile = parser.parse()

    dot_file = stats_file + ".dot"
    pdf_file = dot_file + ".pdf"

    with open(dot_file, "wt") as output:
        dot = DotWriter(output)
        dot.strip = options.strip
        dot.wrap = options.wrap
        dot.show_function_events = [
            TOTAL_TIME,
            TOTAL_TIME_RATIO,
            TIME,
            TIME_RATIO,
        ]

        if options.show_samples:
            dot.show_function_events.append(SAMPLES)

        profile.prune(
            options.node_thres / 100.0,
            options.edge_thres / 100.0,
            [],
            False,
        )

        dot.graph(profile, theme)

    try:
        subprocess.check_call(["dot", "-Tpdf", dot_file, "-o", pdf_file])
    except subprocess.CalledProcessError:
        return {
            "dot_file": dot_file,
            "pdf_file": None,
            "graph_status": "failed_dot_error",
        }
    except OSError:
        return {
            "dot_file": dot_file,
            "pdf_file": None,
            "graph_status": "failed_missing_graphviz",
        }

    return {
        "dot_file": dot_file,
        "pdf_file": pdf_file,
        "graph_status": "success",
    }


def load_yaml_with_cantera(yaml_file):
    result = {
        "yaml_loads": False,
        "yaml_error": "",
        "yaml_species_count": None,
        "yaml_reaction_count": None,
        "yaml_phase_names": "",
        "yaml_surface_phase_count": None,
        "yaml_gas_phase_count": None,
    }

    if yaml_file is None:
        result["yaml_error"] = "No YAML file found."
        return result

    try:
        import cantera as ct
    except Exception as exc:
        result["yaml_error"] = f"Could not import Cantera: {exc}"
        return result

    try:
        gas = ct.Solution(str(yaml_file))
        result["yaml_loads"] = True
        result["yaml_species_count"] = gas.n_species
        result["yaml_reaction_count"] = gas.n_reactions
        result["yaml_phase_names"] = gas.name
        result["yaml_gas_phase_count"] = 1
        result["yaml_surface_phase_count"] = 0
    except Exception as exc:
        result["yaml_error"] = f"Could not load default YAML phase: {exc}"
        return result

    # Try to detect other phases if possible.
    try:
        import yaml as pyyaml

        data = pyyaml.safe_load(Path(yaml_file).read_text(errors="replace"))
        phases = data.get("phases", []) if isinstance(data, dict) else []
        phase_names = []
        surface_count = 0
        gas_count = 0

        for phase in phases:
            name = phase.get("name", "UNKNOWN")
            thermo = str(phase.get("thermo", "")).lower()
            phase_names.append(name)

            if "surface" in thermo or "interface" in thermo:
                surface_count += 1
            if "ideal-gas" in thermo or "gas" in thermo:
                gas_count += 1

        if phase_names:
            result["yaml_phase_names"] = ",".join(phase_names)
            result["yaml_surface_phase_count"] = surface_count
            result["yaml_gas_phase_count"] = gas_count

    except Exception:
        pass

    return result


def convert_chemkin_to_yaml_with_cantera(chemkin_file, species_dict, transport_file, output_yaml):
    if chemkin_file is None:
        return False, "No Chemkin file found."

    cmd = [
        sys.executable,
        "-m",
        "cantera.ck2yaml",
        "--input",
        str(chemkin_file),
        "--output",
        str(output_yaml),
        "--permissive",
    ]

    if species_dict is not None:
        cmd.extend(["--dictionary", str(species_dict)])

    if transport_file is not None:
        cmd.extend(["--transport", str(transport_file)])

    try:
        completed = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except Exception as exc:
        return False, f"Could not run ck2yaml: {exc}"

    if completed.returncode != 0:
        return False, completed.stdout + "\n" + completed.stderr

    return True, completed.stdout + "\n" + completed.stderr


def load_chemkin_with_cantera(run_dir, chemkin_file, species_dict, transport_file):
    result = {
        "chemkin_converts": False,
        "chemkin_loads": False,
        "chemkin_error": "",
        "chemkin_converted_yaml": "",
        "chemkin_species_count": None,
        "chemkin_reaction_count": None,
        "chemkin_phase_names": "",
    }

    if chemkin_file is None:
        result["chemkin_error"] = "No Chemkin file found."
        return result

    try:
        import cantera as ct
    except Exception as exc:
        result["chemkin_error"] = f"Could not import Cantera: {exc}"
        return result

    converted_yaml = Path(run_dir) / "chemkin_converted_by_cantera.yaml"

    ok, msg = convert_chemkin_to_yaml_with_cantera(
        chemkin_file=chemkin_file,
        species_dict=species_dict,
        transport_file=transport_file,
        output_yaml=converted_yaml,
    )

    result["chemkin_converts"] = ok
    result["chemkin_converted_yaml"] = str(converted_yaml)

    if not ok:
        result["chemkin_error"] = msg[-4000:]
        return result

    try:
        gas = ct.Solution(str(converted_yaml))
        result["chemkin_loads"] = True
        result["chemkin_species_count"] = gas.n_species
        result["chemkin_reaction_count"] = gas.n_reactions
        result["chemkin_phase_names"] = gas.name
    except Exception as exc:
        result["chemkin_error"] = f"Converted Chemkin YAML did not load: {exc}"

    return result


def compare_chemistry(run_dir, outputs):
    yaml_result = load_yaml_with_cantera(outputs["yaml_file"])

    chemkin_result = load_chemkin_with_cantera(
        run_dir=run_dir,
        chemkin_file=outputs["chemkin_file"],
        species_dict=outputs["species_dictionary"],
        transport_file=outputs["transport_file"],
    )

    yaml_species = yaml_result["yaml_species_count"]
    chemkin_species = chemkin_result["chemkin_species_count"]

    yaml_rxns = yaml_result["yaml_reaction_count"]
    chemkin_rxns = chemkin_result["chemkin_reaction_count"]

    species_count_match = (
        yaml_species is not None
        and chemkin_species is not None
        and yaml_species == chemkin_species
    )

    reaction_count_match = (
        yaml_rxns is not None
        and chemkin_rxns is not None
        and yaml_rxns == chemkin_rxns
    )

    chemically_equivalent_basic = (
        yaml_result["yaml_loads"]
        and chemkin_result["chemkin_loads"]
        and species_count_match
        and reaction_count_match
    )

    notes = []
    if not yaml_result["yaml_loads"]:
        notes.append("YAML did not load in Cantera.")
    if not chemkin_result["chemkin_loads"]:
        notes.append("Chemkin did not convert/load through Cantera.")
    if yaml_result["yaml_loads"] and chemkin_result["chemkin_loads"]:
        if not species_count_match:
            notes.append(f"Species count mismatch: YAML={yaml_species}, Chemkin={chemkin_species}.")
        if not reaction_count_match:
            notes.append(f"Reaction count mismatch: YAML={yaml_rxns}, Chemkin={chemkin_rxns}.")
    if chemically_equivalent_basic:
        notes.append("Basic Cantera-load/count equivalence passed.")

    return {
        **yaml_result,
        **chemkin_result,
        "yaml_file": str(outputs["yaml_file"]) if outputs["yaml_file"] else "",
        "chemkin_file": str(outputs["chemkin_file"]) if outputs["chemkin_file"] else "",
        "species_dictionary": str(outputs["species_dictionary"]) if outputs["species_dictionary"] else "",
        "transport_file": str(outputs["transport_file"]) if outputs["transport_file"] else "",
        "species_count_match": species_count_match,
        "reaction_count_match": reaction_count_match,
        "chemically_equivalent_basic": chemically_equivalent_basic,
        "chemical_equivalence_notes": " ".join(notes),
    }


def get_cat(profile_data, category, key):
    return profile_data["category_totals"].get(category, {}).get(key, 0.0)


def writer_timing_summary(profile_data):
    yaml_cum = get_cat(profile_data, "yaml_writer", "cumulative_time_s")
    yaml_self = get_cat(profile_data, "yaml_writer", "self_time_s")
    chemkin_cum = get_cat(profile_data, "chemkin_writer", "cumulative_time_s")
    chemkin_self = get_cat(profile_data, "chemkin_writer", "self_time_s")
    output_cum = get_cat(profile_data, "all_output", "cumulative_time_s")
    output_self = get_cat(profile_data, "all_output", "self_time_s")

    ratio = None
    if chemkin_cum > 0:
        ratio = yaml_cum / chemkin_cum

    return {
        "yaml_write_cumulative_s": yaml_cum,
        "yaml_write_self_s": yaml_self,
        "chemkin_write_cumulative_s": chemkin_cum,
        "chemkin_write_self_s": chemkin_self,
        "all_output_cumulative_s": output_cum,
        "all_output_self_s": output_self,
        "yaml_to_chemkin_write_time_ratio": ratio,
    }


def write_function_csv(run_dir, profile_data, git_info, benchmark_name, run_time):
    csv_path = Path(run_dir) / "profile_functions.csv"
    rows = []

    for row in profile_data["function_rows_by_cumulative"]:
        rows.append(
            {
                "benchmark": benchmark_name,
                "run_time": run_time,
                "commit_hash": git_info.get("commit_hash", ""),
                "short_hash": git_info.get("short_hash", ""),
                "branch": git_info.get("branch", ""),
                **row,
            }
        )

    if not rows:
        return csv_path

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return csv_path


def write_report(
    run_dir,
    profile_path,
    git_info,
    profile_data,
    graph_result,
    chemistry,
    writer_timing,
    top_n,
):
    report_path = Path(run_dir) / "analysis_report.txt"

    with open(report_path, "w") as f:
        f.write("=" * 100 + "\n")
        f.write("RMG YAML BENCHMARK ANALYSIS REPORT\n")
        f.write("=" * 100 + "\n\n")

        f.write("RUN INFO\n")
        f.write("-" * 100 + "\n")
        f.write(f"Run directory:       {run_dir}\n")
        f.write(f"Benchmark:           {git_info.get('benchmark', '')}\n")
        f.write(f"SLURM job id:        {git_info.get('slurm_job_id', '')}\n")
        f.write(f"SLURM node:          {git_info.get('slurm_node', '')}\n")
        f.write(f"Profile file:        {profile_path if profile_path else 'MISSING'}\n")
        f.write(f"Total profile time:  {profile_data['total_time_s']:.3f} s\n\n")

        f.write("RMG GIT INFO\n")
        f.write("-" * 100 + "\n")
        for key in ["branch", "commit_hash", "short_hash", "commit_date", "commit_message", "rmg_path"]:
            f.write(f"{key}: {git_info.get(key, '')}\n")
        f.write("\n")

        f.write("PROFILE GRAPH OUTPUT\n")
        f.write("-" * 100 + "\n")
        f.write(f"Graph status:        {graph_result.get('graph_status')}\n")
        f.write(f"DOT file:            {graph_result.get('dot_file')}\n")
        f.write(f"PDF file:            {graph_result.get('pdf_file')}\n\n")

        f.write("WRITER CPU TIME SUMMARY\n")
        f.write("-" * 100 + "\n")
        for key, value in writer_timing.items():
            f.write(f"{key}: {value}\n")
        f.write("\n")

        f.write("CHEMICAL EQUIVALENCE SUMMARY\n")
        f.write("-" * 100 + "\n")
        for key in [
            "yaml_file",
            "chemkin_file",
            "species_dictionary",
            "transport_file",
            "yaml_loads",
            "chemkin_converts",
            "chemkin_loads",
            "yaml_species_count",
            "chemkin_species_count",
            "species_count_match",
            "yaml_reaction_count",
            "chemkin_reaction_count",
            "reaction_count_match",
            "yaml_phase_names",
            "chemkin_phase_names",
            "yaml_surface_phase_count",
            "yaml_gas_phase_count",
            "chemically_equivalent_basic",
            "chemical_equivalence_notes",
        ]:
            f.write(f"{key}: {chemistry.get(key)}\n")

        if chemistry.get("yaml_error"):
            f.write("\nYAML ERROR\n")
            f.write("-" * 100 + "\n")
            f.write(str(chemistry.get("yaml_error")) + "\n")

        if chemistry.get("chemkin_error"):
            f.write("\nCHEMKIN ERROR\n")
            f.write("-" * 100 + "\n")
            f.write(str(chemistry.get("chemkin_error")) + "\n")

        f.write("\nCATEGORY PROFILE SUMMARY\n")
        f.write("-" * 100 + "\n")
        f.write(
            f"{'Category':<28} {'Self s':>12} {'Self %':>10} "
            f"{'Cum s':>12} {'Cum %':>10} {'Calls':>12} {'Funcs':>8}\n"
        )
        f.write("-" * 100 + "\n")

        for row in profile_data["category_rows"]:
            f.write(
                f"{row['category']:<28} "
                f"{row['self_time_s']:>12.3f} "
                f"{row['self_percent']:>9.2f}% "
                f"{row['cumulative_time_s']:>12.3f} "
                f"{row['cumulative_percent']:>9.2f}% "
                f"{row['total_calls']:>12} "
                f"{row['function_count']:>8}\n"
            )

        f.write(f"\nTOP {top_n} FUNCTIONS BY CUMULATIVE TIME\n")
        f.write("-" * 100 + "\n")
        f.write(
            f"{'Cum s':>12} {'Cum %':>10} {'Self s':>12} {'Self %':>10} "
            f"{'Calls':>12} {'Category':<24} Function\n"
        )
        f.write("-" * 100 + "\n")

        for row in profile_data["function_rows_by_cumulative"][:top_n]:
            f.write(
                f"{row['cumulative_time_s']:>12.3f} "
                f"{row['cumulative_percent']:>9.2f}% "
                f"{row['self_time_s']:>12.3f} "
                f"{row['self_percent']:>9.2f}% "
                f"{row['total_calls']:>12} "
                f"{row['category']:<24} "
                f"{row['filename']}:{row['line_number']}:{row['function']}\n"
            )

        f.write(f"\nTOP {top_n} FUNCTIONS BY SELF TIME\n")
        f.write("-" * 100 + "\n")
        f.write(
            f"{'Self s':>12} {'Self %':>10} {'Cum s':>12} {'Cum %':>10} "
            f"{'Calls':>12} {'Category':<24} Function\n"
        )
        f.write("-" * 100 + "\n")

        for row in profile_data["function_rows_by_self"][:top_n]:
            f.write(
                f"{row['self_time_s']:>12.3f} "
                f"{row['self_percent']:>9.2f}% "
                f"{row['cumulative_time_s']:>12.3f} "
                f"{row['cumulative_percent']:>9.2f}% "
                f"{row['total_calls']:>12} "
                f"{row['category']:<24} "
                f"{row['filename']}:{row['line_number']}:{row['function']}\n"
            )

        for category in ["yaml_writer", "chemkin_writer", "all_output"]:
            rows = [
                row for row in profile_data["function_rows_by_cumulative"]
                if row["category"] == category
            ]

            f.write(f"\n{category.upper()} FUNCTIONS\n")
            f.write("-" * 100 + "\n")

            if not rows:
                f.write(f"No functions found for category {category}.\n")
                continue

            for row in rows:
                f.write(
                    f"{row['cumulative_time_s']:>12.3f} s "
                    f"{row['cumulative_percent']:>8.2f}% cumulative | "
                    f"{row['self_time_s']:>12.3f} s "
                    f"{row['self_percent']:>8.2f}% self | "
                    f"{row['total_calls']:>10} calls | "
                    f"{row['filename']}:{row['line_number']}:{row['function']}\n"
                )

    return report_path


def append_history_csv(history_csv, run_dir, git_info, profile_data, graph_result, chemistry, writer_timing):
    history_csv = Path(history_csv)
    history_csv.parent.mkdir(parents=True, exist_ok=True)

    run_time = datetime.datetime.now().isoformat(timespec="seconds")

    row = {
        "analysis_time": run_time,
        "run_dir": str(run_dir),
        "benchmark": git_info.get("benchmark", ""),
        "slurm_job_id": git_info.get("slurm_job_id", ""),
        "slurm_node": git_info.get("slurm_node", ""),
        "rmg_path": git_info.get("rmg_path", ""),
        "branch": git_info.get("branch", ""),
        "commit_hash": git_info.get("commit_hash", ""),
        "short_hash": git_info.get("short_hash", ""),
        "commit_date": git_info.get("commit_date", ""),
        "commit_message": git_info.get("commit_message", ""),
        "total_runtime_s": profile_data["total_time_s"],
        **writer_timing,
        "thermo_cumulative_s": get_cat(profile_data, "thermo", "cumulative_time_s"),
        "thermo_self_s": get_cat(profile_data, "thermo", "self_time_s"),
        "reaction_generation_cumulative_s": get_cat(profile_data, "reaction_generation", "cumulative_time_s"),
        "reaction_generation_self_s": get_cat(profile_data, "reaction_generation", "self_time_s"),
        "model_enlarge_cumulative_s": get_cat(profile_data, "model_enlarge", "cumulative_time_s"),
        "model_enlarge_self_s": get_cat(profile_data, "model_enlarge", "self_time_s"),
        "database_cumulative_s": get_cat(profile_data, "database", "cumulative_time_s"),
        "database_self_s": get_cat(profile_data, "database", "self_time_s"),
        "function_count": len(profile_data["function_rows"]),
        "graph_status": graph_result.get("graph_status"),
        "dot_file": graph_result.get("dot_file"),
        "pdf_file": graph_result.get("pdf_file"),
        **chemistry,
    }

    # Keep CSV compact: errors can be very long.
    for key in ["yaml_error", "chemkin_error"]:
        if key in row and row[key] is not None:
            row[key] = str(row[key])[:1000]

    exists = history_csv.exists()

    with open(history_csv, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)

    return history_csv


def write_json_summary(run_dir, git_info, profile_data, graph_result, chemistry, writer_timing):
    json_path = Path(run_dir) / "analysis_summary.json"

    summary = {
        "git_info": git_info,
        "profile": {
            "total_time_s": profile_data["total_time_s"],
            "category_rows": profile_data["category_rows"],
        },
        "graph": graph_result,
        "chemistry": chemistry,
        "writer_timing": writer_timing,
    }

    json_path.write_text(json.dumps(summary, indent=2, default=str))
    return json_path

def main():
    args = parse_args()

    run_dir = Path(args.run_dir).resolve()
    git_info_path = run_dir / "rmg_git_info.txt"

    git_info = read_key_value_file(git_info_path)
    outputs = find_latest_outputs(run_dir)
    profile_path = find_profile_file(run_dir)

    if profile_path is None:
        if not args.allow_missing_profile:
            raise FileNotFoundError(f"No profile file found in {run_dir}")

        print(f"No profile found in {run_dir} — writing partial analysis.")

        profile_data = {
            "total_time_s": 0.0,
            "function_rows": [],
            "function_rows_by_cumulative": [],
            "function_rows_by_self": [],
            "category_rows": [],
            "category_totals": {},
        }

        graph_result = {
            "dot_file": None,
            "pdf_file": None,
            "graph_status": "skipped_missing_profile",
        }

    else:
        profile_data = process_profile_stats(profile_path)
        graph_result = make_profile_graph_pdf(
            profile_path,
            force_graph_generation=True,
        )

    chemistry = compare_chemistry(run_dir, outputs)
    writer_timing = writer_timing_summary(profile_data)

    report_path = write_report(
        run_dir=run_dir,
        profile_path=profile_path,
        git_info=git_info,
        profile_data=profile_data,
        graph_result=graph_result,
        chemistry=chemistry,
        writer_timing=writer_timing,
        top_n=args.top_n,
    )

    functions_csv = write_function_csv(
        run_dir=run_dir,
        profile_data=profile_data,
        git_info=git_info,
        benchmark_name=git_info.get("benchmark", run_dir.name),
        run_time=datetime.datetime.now().isoformat(timespec="seconds"),
    )

    history_csv = append_history_csv(
        history_csv=args.history_csv,
        run_dir=run_dir,
        git_info=git_info,
        profile_data=profile_data,
        graph_result=graph_result,
        chemistry=chemistry,
        writer_timing=writer_timing,
    )

    json_path = write_json_summary(
        run_dir=run_dir,
        git_info=git_info,
        profile_data=profile_data,
        graph_result=graph_result,
        chemistry=chemistry,
        writer_timing=writer_timing,
    )

    print(f"Wrote report:        {report_path}")
    print(f"Wrote functions CSV: {functions_csv}")
    print(f"Appended history:    {history_csv}")
    print(f"Wrote JSON summary:  {json_path}")
    print(f"Graph status:        {graph_result.get('graph_status')}")

if __name__ == "__main__":
    main()
