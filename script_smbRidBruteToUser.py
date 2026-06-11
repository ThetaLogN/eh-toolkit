#!/usr/bin/env python3

import re
import argparse
import sys


def extract_users(input_file):
    users = []
    pattern = re.compile(r'\\(.+?) \(SidTypeUser\)')

    try:
        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "SidTypeUser" not in line:
                    continue

                match = pattern.search(line)
                if match:
                    username = match.group(1).strip()

                    # Ignora machine account (es. DC1$)
                    if not username.endswith("$"):
                        users.append(username)

    except FileNotFoundError:
        print(f"[-] File non trovato: {input_file}")
        sys.exit(1)

    # Rimuove duplicati mantenendo ordine
    return list(dict.fromkeys(users))


def main():
    parser = argparse.ArgumentParser(
        description="Estrae utenti (SidTypeUser) da output SMB/NetExec/CrackMapExec"
    )

    parser.add_argument(
        "input_file",
        help="File contenente l'output SMB"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="username.txt",
        help="Nome file output (default: username.txt)"
    )

    args = parser.parse_args()

    users = extract_users(args.input_file)

    with open(args.output, "w") as f:
        for user in users:
            f.write(user + "\n")

    print(f"[+] Estratti {len(users)} utenti")
    print(f"[+] Salvati in: {args.output}")


if name == "main":
    main()
