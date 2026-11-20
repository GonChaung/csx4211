# Put the Lab 2 data here

The check-in data is real class data, so it is **not** on GitHub (anyone can read this repository).

1. In MS Teams, open your class team → **Files** → **Class Materials** and download `lab2_data.zip`.
2. Drag `lab2_data.zip` onto this folder (`labs/week02/data/export`) in the codespace Explorer.
3. In the terminal, unzip it here:

```bash
python -m zipfile -e labs/week02/data/export/lab2_data.zip labs/week02/data/export
ls labs/week02/data/export
```

You should see `checkins_2026-11-07.csv`, `roster_v1.csv`, `roster_v2.csv` and `sessions.csv`.
Git ignores the files in this folder, so they are never committed. Do not share them outside the class.
