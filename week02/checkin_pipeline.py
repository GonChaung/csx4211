"""Week 2 - Follow your check-in through the data engineering lifecycle.

On 7 November 2026 you checked in to class with your phone. This pipeline turns
those raw form responses into an attendance list (P = present, A = absent):

  generation      you, on your phone: the class check-in Google Form
  ingestion       extract()    copy the exported CSV files into data/raw/
  storage         load()       load them, unchanged, into tables in a DuckDB file
  transformation  transform()  clean the rows and give every student P or A
                  check()      data quality: which check-ins match nobody?
  serving         serve()      write the attendance report as a CSV file

Data: the real check-ins of 7 November 2026 (names are not included). Because it is
real class data, it is not on GitHub: download lab2_data.zip from MS Teams and unzip
it into data/export/ first (README, Part A). Use the data only for this course.

Run from the repository root:
    python labs/week02/checkin_pipeline.py                            # Part C
    python labs/week02/checkin_pipeline.py --roster v2                # Part E
    python labs/week02/checkin_pipeline.py --roster v2 --id-from email
"""
from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = HERE / "data"
EXPORT_DIR = DATA / "export"  # the instructor's export from Google Sheets (lab2_data.zip in Teams)
RAW_DIR = DATA / "raw"  # your landing zone
DB_FILE = DATA / "week02.duckdb"
REPORT_FILE = DATA / "output" / "attendance_2026-11-07.csv"

ROSTERS = {
    "v1": "class lists printed 6 Nov: CSX4211 only",
    "v2": "class lists printed 6 and 7 Nov: CSX4211 + ITX4211",
}


def extract(roster: str) -> dict[str, Path]:
    """Ingestion: copy the exported files into the landing zone data/raw/."""
    files = {
        "checkins": "checkins_2026-11-07.csv",
        "roster": f"roster_{roster}.csv",
        "sessions": "sessions.csv",
    }
    missing = [file for file in files.values() if not (EXPORT_DIR / file).exists()]
    if missing:
        raise SystemExit(
            f"[extract]   missing in {EXPORT_DIR.relative_to(REPO).as_posix()}/: {', '.join(missing)}\n"
            "            Download lab2_data.zip from MS Teams and unzip it there (README, Part A, step 3)."
        )
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, file in files.items():
        paths[name] = RAW_DIR / file
        shutil.copyfile(EXPORT_DIR / file, paths[name])
    print(f"[extract]   copied {', '.join(files.values())} into {RAW_DIR.relative_to(REPO).as_posix()}/")
    return paths


def load(con: duckdb.DuckDBPyConnection, paths: dict[str, Path]) -> None:
    """Storage: load each raw file into its own table, unchanged (every column as text)."""
    for name, path in paths.items():
        con.execute(
            f"CREATE OR REPLACE TABLE raw_{name} AS "
            f"SELECT * FROM read_csv('{path.as_posix()}', all_varchar = true)"
        )
        rows = con.execute(f"SELECT count(*) FROM raw_{name}").fetchone()[0]
        print(f"[load]      {rows:>3} rows loaded into table raw_{name}")


def transform(con: duckdb.DuckDBPyConnection, id_from: str) -> None:
    """Transformation: clean the raw rows, then give every student on the roster P or A."""
    # 1. Clean the form responses: real timestamps, the section number,
    #    and two versions of the student ID: the one typed and the one in the e-mail address.
    con.execute(r"""
        CREATE OR REPLACE TABLE checkins AS
        SELECT strptime("Timestamp", '%m/%d/%Y %H:%M:%S')      AS checked_in_at,
               regexp_extract("Your section", '\d{3}')          AS section,
               trim("Student ID")                               AS typed_id,
               regexp_extract("Email Address", 'u(\d{7})@', 1)  AS email_id,
               trim("Today's code")                             AS code
        FROM raw_checkins
    """)
    # 2. The roster: who should be in class.
    con.execute("""
        CREATE OR REPLACE TABLE roster AS
        SELECT section, trim(student_id) AS student_id, course
        FROM raw_roster
    """)
    # 3. The real classes. The 6 Nov row was the instructor's test, so it is left out.
    con.execute("""
        CREATE OR REPLACE TABLE classes AS
        SELECT session_id, section,
               CAST(class_date AS DATE)      AS class_date,
               CAST(opened_at  AS TIMESTAMP) AS opened_at,
               CAST(closes_at  AS TIMESTAMP) AS closes_at,
               code
        FROM raw_sessions
        WHERE coalesce(type, '') <> 'test'
    """)
    # 4. A check-in counts when the section and the code are right and the form was open.
    student_id = "c.email_id" if id_from == "email" else "c.typed_id"
    con.execute(f"""
        CREATE OR REPLACE TABLE valid_checkins AS
        SELECT k.class_date, c.section, {student_id} AS student_id, c.checked_in_at
        FROM checkins AS c
        JOIN classes AS k
          ON  c.section = k.section
          AND c.code    = k.code
          AND c.checked_in_at BETWEEN k.opened_at AND k.closes_at
    """)
    # 5. P or A for every student on the roster, in every class of their section.
    #    Absent students have no check-in row at all. The LEFT JOIN keeps them anyway.
    con.execute("""
        CREATE OR REPLACE TABLE attendance AS
        SELECT r.section, k.class_date, r.student_id, r.course,
               CASE WHEN count(v.student_id) > 0 THEN 'P' ELSE 'A' END AS status,
               min(v.checked_in_at) AS checked_in_at
        FROM roster AS r
        JOIN classes AS k
          ON k.section = r.section
        LEFT JOIN valid_checkins AS v
          ON  v.student_id = r.student_id
          AND v.section    = r.section
          AND v.class_date = k.class_date
        GROUP BY r.section, k.class_date, r.student_id, r.course
        ORDER BY r.section, k.class_date, r.student_id
    """)
    print("[transform] built tables checkins, roster, classes, valid_checkins, attendance")


def rows(n: int) -> str:
    return f"{n} check-in{'' if n == 1 else 's'}"


def check(con: duckdb.DuckDBPyConnection, id_from: str) -> None:
    """Data quality: problems the attendance table alone would hide."""
    con.execute("""
        CREATE OR REPLACE TABLE unmatched_checkins AS
        SELECT v.*
        FROM valid_checkins AS v
        LEFT JOIN roster AS r
          ON r.student_id = v.student_id AND r.section = v.section
        WHERE r.student_id IS NULL
        ORDER BY v.checked_in_at
    """)
    invalid = con.execute(
        "SELECT (SELECT count(*) FROM checkins) - (SELECT count(*) FROM valid_checkins)"
    ).fetchone()[0]
    unmatched = con.execute("SELECT count(*) FROM unmatched_checkins").fetchone()[0]
    typo = con.execute("SELECT count(*) FROM checkins WHERE typed_id <> email_id").fetchone()[0]
    flag = "WARNING" if invalid else "ok"
    print(f"[check]     {flag}: {rows(invalid)} with a wrong code or outside the open time")
    flag = "WARNING" if unmatched else "ok"
    print(f"[check]     {flag}: {rows(unmatched)} matching no student on the roster (table unmatched_checkins)")
    if id_from == "email":
        print(f"[check]     ok: {rows(typo)} where the typed ID is not the ID in the e-mail address"
              " (handled: the student ID now comes from the e-mail)")
    else:
        flag = "WARNING" if typo else "ok"
        print(f"[check]     {flag}: {rows(typo)} where the typed ID is not the ID in the e-mail address")


def serve(con: duckdb.DuckDBPyConnection) -> None:
    """Serving: publish the attendance list as a CSV file and show a summary."""
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY attendance TO '{REPORT_FILE.as_posix()}' (HEADER, DELIMITER ',')")
    print(f"[serve]     report written to {REPORT_FILE.relative_to(REPO).as_posix()}")
    con.sql("""
        SELECT section,
               count(*) FILTER (WHERE status = 'P') AS present,
               count(*) FILTER (WHERE status = 'A') AS absent,
               count(*)                             AS students
        FROM attendance
        GROUP BY section
        ORDER BY section
    """).show()


def signature() -> str:
    """Who ran the pipeline, in which codespace and when: your screenshots show it."""
    try:
        when = f"{datetime.now(ZoneInfo('Asia/Bangkok')):%Y-%m-%d %H:%M} Bangkok time"
    except Exception:  # no time zone data on this computer
        when = f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC"
    user = os.environ.get("GITHUB_USER")  # set by GitHub in every codespace
    if user:
        return f"run by @{user} in codespace {os.environ.get('CODESPACE_NAME', '?')} on {when}"
    return f"run outside a codespace on {when}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Week 2 check-in pipeline")
    parser.add_argument("--roster", choices=sorted(ROSTERS), default="v1",
                        help="which class list to use (default: v1)")
    parser.add_argument("--id-from", choices=["typed", "email"], default="typed",
                        help="take the student ID from what was typed or from the e-mail address")
    args = parser.parse_args()
    print(f"Settings: roster {args.roster} ({ROSTERS[args.roster]}), student ID from: {args.id_from}\n")

    paths = extract(args.roster)
    with duckdb.connect(str(DB_FILE)) as con:
        load(con, paths)
        transform(con, args.id_from)
        check(con, args.id_from)
        serve(con)
    print(f"Pipeline finished: {signature()}")
    print("Explore the data with:  python labs/week02/query.py")


if __name__ == "__main__":
    main()
