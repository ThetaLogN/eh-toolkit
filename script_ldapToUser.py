import sys
import os
import argparse


def extract_users(input_file):
    if not os.path.exists(input_file):
        print(f"[-] Errore: Il file '{input_file}' non esiste!")
        sys.exit(1)

    usernames = []
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # Se la riga contiene il comando nxc lanciato dall'utente, la salta del tutto
            if "nxc ldap" in line or "cme ldap" in line:
                continue

            parts = line.split()

            if len(parts) >= 5:
                user = parts[4]

                # Filtra intestazioni, flag rimasti e messaggi di stato
                if user not in ["-Username-", "Enumerated", "[*]", "[+]", "-u", "-p"]:
                    if user not in usernames:
                        usernames.append(user)
    return usernames


def main():
    parser = argparse.ArgumentParser(
        description="Estrae ed elenca in modo pulito gli username dall'output di un comando NetExec/CME LDAP."
    )
    parser.add_argument(
        "input_file",
        help="Il file di testo contenente l'output grezzo di NetExec/CME LDAP (es. nxc ldap ... --users)"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="users.txt",
        help="Il file di output in cui salvare gli username estratti (default: users.txt)"
    )

    args = parser.parse_args()

    usernames = extract_users(args.input_file)

    # Salva i risultati puliti
    with open(args.output, "w", encoding="utf-8") as f_out:
        for user in usernames:
            f_out.write(user + "\n")

    print(f"[+] Estrazione completata! {len(usernames)} utenti puliti salvati in '{args.output}'.")


if __name__ == "__main__":
    main()
