import sys
import os

# Controlla se l'utente ha chiesto l'aiuto (-h o --help)
if "-h" in sys.argv or "--help" in sys.argv:
    print(f"Uso: python3 {sys.argv[0]} <file_di_input>")
    print("\nDescrizione:")
    print("  Estrae ed elenca in modo pulito gli username dall'output di un comando NetExec/CME LDAP.")
    print("\nArgomenti:")
    print("  <file_di_input>   Il file di testo contenente l'output grezzo di 'nxc ldap ... --users'")
    sys.exit(0)

# Controlla se non è stato passato l'argomento obbligatorio
if len(sys.argv) < 2:
    print(f"[-] Errore: Manca il file di input.")
    print(f"Uso corretto: python3 {sys.argv[0]} <file_di_input> (Usa -h per l'aiuto)")
    sys.exit(1)

# Prende il file di input dall'argomento del terminale
input_file = sys.argv[1]
output_file = "users.txt"

# Controlla se il file inserito esiste davvero
if not os.path.exists(input_file):
    print(f"[-] Errore: Il file '{input_file}' non esiste nella cartella corrente!")
    sys.exit(1)

usernames = []

with open(input_file, "r", encoding="utf-8") as f:
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

# Salva i risultati puliti
with open(output_file, "w", encoding="utf-8") as f_out:
    for user in usernames:
        f_out.write(user + "\n")

print(f"[+] Estrazione completata! {len(usernames)} utenti puliti salvati in '{output_file}'.")
