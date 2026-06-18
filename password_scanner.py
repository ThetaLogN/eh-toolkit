import os
import re
import math
import argparse

# 1. Pattern estesi basati su standard industriali (es. rilevamento tool di sniffing/gitleaks)
ADVANCED_PATTERNS = {
    "Chiave Privata (RSA/SSH/ECC)": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
    "Password/Segreto Generico (Assegnazione)": r"(?i)(password|passwd|secret|api_key|apikey|secret_key|private_key|db_pass|credential)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.\@\!#\$%\^&\*\(\)\+]+)['\"]?",
    "Token AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Chiave Privata AWS Secret": r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?([a-zA-Z0-9/+=]{40})['\"]?",
    "Token JWT (JSON Web Token)": r"eyJhbGciOi[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+",
    "Stringa di connessione Database": r"(mongodb\+srv|postgres|mysql|sqlite|oracle|mssql)://[a-zA-Z0-9_]+:[^@]+@[a-zA-Z0-9.-]+",
    "Slack OAuth Token": r"xox[bapr]-[0-9]{11,12}-[a-zA-Z0-9]{24,48}",
    "GitHub Personal Access Token": r"ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{82}",
    "Google API Key": r"AIza[0-9A-Za-z-_]{35}"
}

# Esclusioni per evitare crash e rallentamenti inutili
IGNORE_DIRS = {'.git', 'node_modules', 'venv', 'venvscript', '__pycache__', '.idea', '.vscode'}
IGNORE_EXTENSIONS = {'.exe', '.dll', '.so', '.dylib', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.mp4', '.mp3', '.pdf', '.woff', '.woff2', '.ico'}

SCRIPT_NAME = os.path.basename(__file__)


def calculate_shannon_entropy(data):
    """Calcola l'entropia di Shannon di una stringa per verificare la casualità (es. chiavi generate)."""
    if not data:
        return 0
    entropy = 0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        entropy -= p_x * math.log(p_x, 2)
    return entropy


def check_high_entropy_words(line, threshold=4.5):
    """Scompone la riga in parole e cerca stringhe ad alta entropia (potenziali password/chiavi offuscate)."""
    # Raccoglie stringhe alfanumeriche lunghe almeno 8 caratteri
    words = re.findall(r'[a-zA-Z0-9/+=-]{8,}', line)
    high_entropy_matches = []
    for word in words:
        # Evita di segnalare stringhe standard ripetitive (es. "AAAAAAA") o pattern noti
        if len(set(word)) < 4:
            continue
        entropy = calculate_shannon_entropy(word)
        if entropy > threshold:
            high_entropy_matches.append((word, round(entropy, 2)))
    return high_entropy_matches


def scan_file(file_path, verbose=False):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line:
                    continue

                # A. Verifica tramite Regex
                for name, pattern in ADVANCED_PATTERNS.items():
                    match = re.search(pattern, clean_line)
                    if match:
                        print(f"[!] REGEX MATCH RILEVATO: [{name}]")
                        print(f"    File:  {file_path}")
                        print(f"    Linea {line_num}: {clean_line[:120]}")
                        print("-" * 60)
                        return  # Evita duplicati sulla stessa riga

                # B. Verifica tramite Entropia (Trova ciò che le regex non coprono)
                high_entropy_secrets = check_high_entropy_words(clean_line)
                for secret, ent_score in high_entropy_secrets:
                    # Filtro per evitare falsi positivi grossolani nel codice (es. nomi di funzioni/classi lunghe)
                    if any(kw in clean_line.lower() for kw in ["def ", "class ", "import ", "include"]):
                        continue
                    print(f"[?] ALTA ENTROPIA RILEVATA (Score: {ent_score})")
                    print(f"    File:  {file_path}")
                    print(f"    Linea {line_num}: Strumento casuale rilevato -> {secret[:50]}")
                    print(f"    Contesto: {clean_line[:120]}")
                    print("-" * 60)

    except Exception as e:
        if verbose:
            print(f"[-] Errore durante la scansione del file {file_path}: {e}")


def start_scan(target_directory, verbose=False):
    print(f"[*] Avvio scansione ad alta robustezza in: {target_directory}")
    print("[*] Nota: Verranno analizzati pattern specifici e anomalie ad alta entropia.")
    print("=" * 70)

    for root, dirs, files in os.walk(target_directory):
        # Modifica in-place per saltare le directory ignorate
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file == SCRIPT_NAME:
                continue
            if any(file.endswith(ext) for ext in IGNORE_EXTENSIONS):
                continue

            file_path = os.path.join(root, file)
            scan_file(file_path, verbose=verbose)


def main():
    parser = argparse.ArgumentParser(
        description="Analizza file e cartelle alla ricerca di password, chiavi API o dati ad alta entropia."
    )
    parser.add_argument(
        "target_directory",
        nargs="?",
        default=".",
        help="Il percorso della cartella o del file da scansionare (default: cartella corrente '.')"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Mostra gli errori di lettura dei file (es. permessi negati)"
    )

    args = parser.parse_args()

    if os.path.exists(args.target_directory):
        start_scan(args.target_directory, verbose=args.verbose)
        print("[*] Scansione terminata.")
    else:
        print(f"[-] Percorso inesistente: {args.target_directory}")


if __name__ == "__main__":
    main()
