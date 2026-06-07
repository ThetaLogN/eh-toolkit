# Nome del file di input e di output
input_file = "output_nxc.txt"
output_file = "users.txt"

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
