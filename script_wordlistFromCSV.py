import csv
from itertools import product

input_file = "staff-directory.csv"
output_file = "usernames.txt"

usernames = set()

separators = ["", ".", "_", "-"]

with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        first = row["FirstName"].strip().lower()
        last = row["LastName"].strip().lower()

        fi = first[0]
        li = last[0]

        patterns = [
            (first, last),
            (last, first),
            (fi, last),
            (first, li),
            (last, fi),
            (fi, ".", last),
            (first, ".", li),
            (last, ".", fi),
        ]

        # Base names
        usernames.add(first)
        usernames.add(last)
        usernames.add(fi + li)

        # Generate separator variations
        for sep in separators:
            usernames.add(f"{first}{sep}{last}")
            usernames.add(f"{last}{sep}{first}")
            usernames.add(f"{fi}{sep}{last}")
            usernames.add(f"{first}{sep}{li}")
            usernames.add(f"{last}{sep}{fi}")

# Salva
with open(output_file, "w", encoding="utf-8") as f:
    for u in sorted(usernames):
        f.write(u + "\n")

print(f"Generati {len(usernames)} username")
