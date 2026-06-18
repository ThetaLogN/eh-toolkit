# eh-toolkit

Una raccolta di script di utilità per attività di Ethical Hacking, OSINT e parsing di output generati da strumenti di sicurezza (es. NetExec, CrackMapExec, ecc.).

Ogni script è indipendente, strutturato con gestione degli argomenti da riga di comando (`argparse`) e pensato per essere facilmente integrabile nei flussi di lavoro di penetration testing.

---

## Indice dei Contenuti
1. [Requisiti e Installazione](#requisiti-e-installazione)
2. [Descrizione degli Script](#descrizione-degli-script)
   - [analizzaWeb.py](#analizzawebpy)
   - [password_scanner.py](#password_scannerpy)
   - [script_ldapToUser.py](#script_ldapto-userpy)
   - [script_smbRidBruteToUser.py](#script_smbridbruteto-userpy)
   - [script_wordlistFromCSV.py](#script_wordlistfromcsvpy)
   - [ad_password_spray.py](#ad_password_spraypy)
   - [document_metadata_extractor.py](#document_metadata_extractorpy)
   - [linux_privesc_helper.py](#linux_privesc_helperpy)
   - [container_audit.sh](#container_auditsh)
3. [Download di Strumenti Esterni](#download-di-strumenti-esterni)
4. [Cheat Sheet Comandi PowerShell (powershell_commands.md)](file:///Users/giorgiomartucci/eh-toolkit/eh-toolkit/powershell_commands.md)
5. [Cheat Sheet Upgrade Shell (shell_upgrade.md)](file:///Users/giorgiomartucci/eh-toolkit/eh-toolkit/shell_upgrade.md)

---

## Requisiti e Installazione

Il toolkit è compatibile con Python 3. Per installare le librerie esterne richieste (es. `requests`, `BeautifulSoup`, `ldap3`, `pypdf`), esegui:

```bash
pip install -r requirements.txt
```

*(Nota: Lo script `linux_privesc_helper.py` è scritto in Python nativo e non richiede alcuna libreria aggiuntiva).*

---

## Descrizione degli Script

### analizzaWeb.py
Esegue il download e l'analisi di una pagina HTML a partire da un URL. Estrae informazioni utili tra cui:
* Protocolli di rete rilevati nei link o nel testo.
* Nomi di software e relative versioni (es. `Apache/2.4.41`).
* Nomi utente e menzioni (pattern `@username`).
* Indirizzi email e indirizzi IP trovati.

**Uso:**
```bash
python3 analizzaWeb.py <URL>
```
*Esempio:*
```bash
python3 analizzaWeb.py https://example.com
```

---

### password_scanner.py
Analizza in modo ricorsivo file e cartelle alla ricerca di potenziali credenziali o segreti esposti. Utilizza sia pattern Regex avanzati (es. token AWS, chiavi private, token JWT, personal access token GitHub) sia il calcolo dell'entropia di Shannon per rilevare stringhe casuali ad alta entropia (es. password robuste offuscate).

**Uso:**
```bash
python3 password_scanner.py [cartella_o_file] [-v]
```
* `-v`, `--verbose`: Mostra eventuali errori di lettura del file system (es. file protetti o permessi negati).

*Esempio:*
```bash
python3 password_scanner.py . -v
```

---

### script_ldapToUser.py
Analizza l'output grezzo salvato da un comando NetExec (`nxc ldap ... --users`) o CrackMapExec e ne estrae gli username in modo pulito, filtrando intestazioni, flag di stato e rimuovendo eventuali duplicati.

**Uso:**
```bash
python3 script_ldapToUser.py <file_di_input> [-o <file_di_output>]
```
* `-o`, `--output`: Definisce il nome del file di testo in cui salvare i risultati (default: `users.txt`).

*Esempio:*
```bash
python3 script_ldapToUser.py output_ldap.txt -o usernames_ldap.txt
```

---

### script_smbRidBruteToUser.py
Estrae ed elenca in modo pulito gli username di tipo `SidTypeUser` a partire dall'output di una scansione SMB/RID Brute force (es. tramite NetExec/CME). Esclude automaticamente i machine account (quelli che terminano con `$`) e rimuove i duplicati mantenendo l'ordine originario.

**Uso:**
```bash
python3 script_smbRidBruteToUser.py <file_di_input> [-o <file_di_output>]
```
* `-o`, `--output`: Nome del file TXT di output (default: `username.txt`).

*Esempio:*
```bash
python3 script_smbRidBruteToUser.py output_smb.txt -o usernames_smb.txt
```

---

### script_wordlistFromCSV.py
Genera una lista estesa di potenziali username (wordlist) partendo da un file CSV contenente i nomi e i cognomi dello staff. Genera combinazioni multiple combinando iniziali, nomi interi e cognomi con diversi separatori (`.`, `_`, `-` o nessuno).

**Uso:**
```bash
python3 script_wordlistFromCSV.py <file_csv> [-o <file_output>] [--first-col <nome_colonna>] [--last-col <nome_colonna>]
```
* `-o`, `--output`: Nome del file TXT di output (default: `usernames.txt`).
* `--first-col`: Nome dell'intestazione di colonna per il Nome (default: `FirstName`).
* `--last-col`: Nome dell'intestazione di colonna per il Cognome (default: `LastName`).

*Esempio:*
```bash
python3 script_wordlistFromCSV.py dipendenti.csv -o wordlist_utenti.txt --first-col "Nome" --last-col "Cognome"
```

---

### ad_password_spray.py
Esegue un attacco di password spraying via LDAP/LDAPS contro un Domain Controller Active Directory. Per ogni tentativo fallito, decodifica il codice diagnostico AD per indicare se la password è errata, se l'account è bloccato (lockout), disabilitato, scaduto o se richiede il reset della password al prossimo accesso.

**Uso:**
```bash
python3 ad_password_spray.py <dc_ip> <user_list> <password> [-d <dominio>] [--delay <secondi>] [-o <file_output>] [--ssl]
```
* `-d`, `--domain`: Dominio AD (es. `corp.local`) per formattare gli utenti come UPN (`utente@dominio`).
* `--delay`: Ritardo in secondi tra i tentativi per evitare lockout o rumore eccessivo (default: `0.0`).
* `-o`, `--output`: File per registrare i login riusciti (default: `valid_credentials.txt`).
* `--ssl`: Forza l'utilizzo di LDAPS (porta 636) anziché LDAP standard (porta 389).

*Esempio:*
```bash
python3 ad_password_spray.py 10.10.10.10 utenti_ad.txt Winter2026! -d corp.local --delay 1.5 -o credenziali_valide.txt
```

---

### document_metadata_extractor.py
Scansiona un file o un'intera cartella ricorsivamente alla ricerca di file Office (.docx, .xlsx, .pptx) e PDF per estrarre metadati sensibili (creatore, autore della modifica, data creazione, data modifica, software utilizzato e azienda/organizzazione). 
*Per i file Office la lettura dell'XML è implementata nativamente, mentre per i PDF richiede la libreria `pypdf`.*

**Uso:**
```bash
python3 document_metadata_extractor.py <percorso_target> [-o <file_output>]
```
* `-o`, `--output`: Salva i risultati in formato CSV o JSON (in base all'estensione fornita, es. `report.csv` o `report.json`).

*Esempio:*
```bash
python3 document_metadata_extractor.py /var/www/uploads/ -o metadati_estratti.csv
```

---

### linux_privesc_helper.py
Esegue una scansione locale non intrusiva alla ricerca di vettori di escalation dei privilegi su macchine Linux. Non richiede librerie di terze parti (Python standard puro) e verifica:
* Informazioni utente/sistema e appartenenza a gruppi sensibili (es. `docker`, `lxd`, `shadow`).
* Privilegi sudo disponibili senza password (tramite `sudo -n -l`).
* Presenza di file **SUID/SGID** mappati rispetto a binari noti vulnerabili su GTFOBins.
* File di sistema critici con permessi di scrittura aperti.
* Percorsi degli eseguibili nei **cronjob** di sistema e permessi di scrittura ad essi associati.
* Connessioni TCP attive decodificate direttamente da `/proc/net/tcp` (evidenziando i listener locali non esposti).

**Uso:**
```bash
python3 linux_privesc_helper.py
```
*(Nota: Lo script può essere trasferito e avviato direttamente come utente limitato su una macchina Linux target).*

---

### container_audit.sh
Esegue un audit locale di sicurezza avanzato all'interno di un container Linux (es. Docker) per valutare il livello di isolamento e hardening. Verifica:
* Contesto utente e mappatura degli User Namespace (root mapping).
* Condivisione o isolamento dei Namespace dell'host (PID, Network).
* Attivazione e configurazione di LSM (AppArmor e filtri Seccomp).
* Presenza di Mount point host esposti e sensibili (es. `/var/run/docker.sock`, `/etc/shadow`, `/home`).
* Accesso diretto a dispositivi a blocchi del disco (es. `/dev/sda`) e presenza di Capabilities pericolose (es. `SYS_ADMIN`, `SYS_PTRACE`, `SYS_MODULE`).

**Uso:**
```bash
chmod +x container_audit.sh
./container_audit.sh
```

---

## Download di Strumenti Esterni

Il repository include uno script di utilità bash chiamato `get_external_tools.sh` per scaricare automaticamente l'ultima versione dei migliori strumenti esterni per Windows e Linux direttamente dalle release ufficiali dei rispettivi autori.

I file scaricati vengono posizionati nella cartella `bin/` (strutturata in `bin/linux` e `bin/windows`) e sono **automaticamente esclusi da Git** tramite il file `.gitignore` per evitare di caricare accidentalmente file binari pesanti o segnalati dagli antivirus.

**Strumenti scaricati:**
* **LinPEAS (`linpeas.sh`)**: Script per privilege escalation locale su Linux.
* **git-dumper**: Tool in Python per scaricare repository `.git` esposti pubblicamente sui server web.
* **WinPEAS (`winPEASany.exe`, `winPEAS.bat`)**: Strumenti per privilege escalation locale su Windows.
* **SharpGPOAbuse (`SharpGPOAbuse.exe`)**: Strumento in C# per abusare dei permessi GPO su Active Directory.
* **Seatbelt (`Seatbelt.exe`)**: Utility C# per raccogliere informazioni sulla sicurezza locale del sistema Windows.
* **PrintSpoofer (`PrintSpoofer64.exe`)**: Exploit locale per elevare i privilegi da Service Account a SYSTEM su Windows Server.

**Uso:**
```bash
chmod +x get_external_tools.sh
./get_external_tools.sh
```
Una volta scaricati, puoi esporre la cartella `bin/` usando un server HTTP Python per caricarli sui tuoi target:
```bash
python3 -m http.server 80
```
