import os
import re

# Definiamo i pattern regex per cercare potenziali credenziali
PATTERNS = {
    "Chiave Privata RSA/SSH": r"-----BEGIN [A-Z]+ PRIVATE KEY-----",
    "API Key generica / Password esplicita": r"(?i)(password|passwd|secret|api_key|apikey|secret_key|private_key)\s*[:=]\s*['\"]([^'\"]+)['\"]",
    "Token AWS": r"AKIA[0-9A-Z]{16}",
    "Slack Token": r"xoxb-[0-9]{11}-[a-zA-Z0-9]{24}",
    "Stringa di connessione DB": r"mongodb\+srv://|postgres://|mysql://",
}

# Estensioni di file da ignorare per evitare falsi positivi o file binari pesanti
IGNORE_EXTENSIONS = {'.exe', '.dll', '.so', '.dylib', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.mp4', '.mp3'}

def scan_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                clean_line = line.strip()
                for name, pattern in PATTERNS.items():
                    match = re.search(pattern, clean_line)
                    if match:
                        print(f"[!] TROVATO [{name}]")
                        print(f"    File: {file_path}")
                        print(f"    Linea {line_num}: {clean_line[:100]}") # Tronca a 100 caratteri per leggibilità
                        print("-" * 50)
    except Exception as e:
        # Ignora file non leggibili (es. permessi negati su singoli file)
        pass

def start_scan(target_directory):
    print(f"[*] Inizio scansione nella directory: {target_directory}")
    print("=" * 60)
    
    for root, dirs, files in os.walk(target_directory):
        for file in files:
            # Salta i file con estensioni binarie note
            if any(file.endswith(ext) for ext in IGNORE_EXTENSIONS):
                continue
                
            file_path = os.path.join(root, file)
            scan_file(file_path)

if __name__ == "__main__":
    # Inserisci qui il percorso della cartella che vuoi analizzare.
    # '.' indica la cartella corrente in cui ti trovi nel terminale.
    target_path = input("Inserisci il percorso assoluto della cartella da scansionare (premi Invio per la cartella corrente): ")
    if not target_path.strip():
        target_path = "."
        
    if os.path.exists(target_path):
        start_scan(target_path)
        print("[*] Scansione completata.")
    else:
        print("[-] Percorso non valido.")
