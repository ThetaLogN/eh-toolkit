import csv
import sys
import os
import argparse


def generate_wordlist(input_file, first_col, last_col):
    if not os.path.exists(input_file):
        print(f"[-] Errore: Il file CSV '{input_file}' non esiste!")
        sys.exit(1)

    usernames = set()
    separators = ["", ".", "_", "-"]

    try:
        with open(input_file, newline='', encoding='utf-8', errors='ignore') as csvfile:
            reader = csv.DictReader(csvfile)

            # Verifichiamo la presenza delle colonne
            if reader.fieldnames is None:
                print(f"[-] Errore: Il file CSV '{input_file}' è vuoto o non valido.")
                sys.exit(1)

            if first_col not in reader.fieldnames or last_col not in reader.fieldnames:
                print(f"[-] Errore: Colonne '{first_col}' e/o '{last_col}' non trovate nel file CSV.")
                print(f"    Colonne disponibili: {', '.join(reader.fieldnames)}")
                sys.exit(1)

            for row in reader:
                # Gestiamo il caso in cui alcune righe abbiano valori nulli o mancanti
                if not row.get(first_col) or not row.get(last_col):
                    continue

                first = row[first_col].strip().lower()
                last = row[last_col].strip().lower()

                if not first or not last:
                    continue

                fi = first[0]
                li = last[0]

                # Nomi di base
                usernames.add(first)
                usernames.add(last)
                usernames.add(fi + li)

                # Genera combinazioni con i separatori
                for sep in separators:
                    usernames.add(f"{first}{sep}{last}")
                    usernames.add(f"{last}{sep}{first}")
                    usernames.add(f"{fi}{sep}{last}")
                    usernames.add(f"{first}{sep}{li}")
                    usernames.add(f"{last}{sep}{fi}")
    except Exception as e:
        print(f"[-] Errore durante l'elaborazione del file CSV: {e}")
        sys.exit(1)

    return usernames


def main():
    parser = argparse.ArgumentParser(
        description="Genera una lista di potenziali username a partire da un file CSV contenente nomi e cognomi."
    )
    parser.add_argument(
        "input_file",
        help="Il file CSV di input contenente l'elenco dello staff (es. staff-directory.csv)"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="usernames.txt",
        help="Nome del file TXT di output in cui salvare gli username generati (default: usernames.txt)"
    )
    parser.add_argument(
        "--first-col",
        default="FirstName",
        help="Nome della colonna per il Nome nel file CSV (default: FirstName)"
    )
    parser.add_argument(
        "--last-col",
        default="LastName",
        help="Nome della colonna per il Cognome nel file CSV (default: LastName)"
    )

    args = parser.parse_args()

    usernames = generate_wordlist(args.input_file, args.first_col, args.last_col)

    # Salva
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            for u in sorted(usernames):
                f.write(u + "\n")
        print(f"[+] Generati {len(usernames)} username salvati in '{args.output}'")
    except Exception as e:
        print(f"[-] Errore durante la scrittura del file di output: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
