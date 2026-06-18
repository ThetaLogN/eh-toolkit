#!/bin/bash

# Abortiamo in caso di errore generico
set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0;36m' # No Color (Cyan-ish)
RESET='\033[0m'

echo -e "${BLUE}[*] Inizializzazione download degli strumenti esterni...${RESET}"

# Verifica presenza di curl
if ! command -v curl &> /dev/null; then
    echo -e "${RED}[-] Errore: 'curl' non è installato sul sistema. Installalo per continuare.${RESET}"
    exit 1
fi

# Creazione cartelle
echo -e "${NC}[*] Creazione della struttura delle directory 'bin/'...${RESET}"
mkdir -p bin/linux bin/windows

# ----------------- LINUX TOOLS -----------------
echo -e "${BLUE}\n=== STRUMENTI LINUX ===${RESET}"

# 1. LinPEAS
echo -e "${NC}[*] Download di LinPEAS (linpeas.sh)...${RESET}"
curl -L -s -f "https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh" -o "bin/linux/linpeas.sh"
chmod +x bin/linux/linpeas.sh
echo -e "${GREEN}[+] LinPEAS salvato in bin/linux/linpeas.sh (eseguibile)${RESET}"

# 2. Git-Dumper
echo -e "${NC}[*] Clono git-dumper...${RESET}"
if [ -d "bin/linux/git-dumper" ]; then
    rm -rf bin/linux/git-dumper
fi
git clone --depth 1 "https://github.com/arthaud/git-dumper.git" "bin/linux/git-dumper"
echo -e "${GREEN}[+] git-dumper clonato in bin/linux/git-dumper/${RESET}"

# ----------------- WINDOWS TOOLS -----------------
echo -e "${BLUE}\n=== STRUMENTI WINDOWS ===${RESET}"

# 3. WinPEAS EXE
echo -e "${NC}[*] Download di WinPEAS (winPEASany.exe)...${RESET}"
curl -L -s -f "https://github.com/carlospolop/PEASS-ng/releases/latest/download/winPEASx64.exe" -o "bin/windows/winPEASx64.exe"
echo -e "${GREEN}[+] WinPEAS (EXE) salvato in bin/windows/winPEASx64.exe${RESET}"

# 5. SharpGPOAbuse (C# tool da SharpCollection)
echo -e "${NC}[*] Download di SharpGPOAbuse.exe...${RESET}"
curl -L -s -f "https://github.com/Flangvik/SharpCollection/blob/master/NetFramework_4.0_x64/SharpGPOAbuse.exe" -o "bin/windows/SharpGPOAbuse.exe"
echo -e "${GREEN}[+] SharpGPOAbuse salvato in bin/windows/SharpGPOAbuse.exe${RESET}"

# 6. Seatbelt (C# tool da SharpCollection)
echo -e "${NC}[*] Download di Seatbelt.exe...${RESET}"
curl -L -s -f "https://github.com/Flangvik/SharpCollection/raw/master/NetFramework_4.7_Any/Seatbelt.exe" -o "bin/windows/Seatbelt.exe"
echo -e "${GREEN}[+] Seatbelt salvato in bin/windows/Seatbelt.exe${RESET}"

# 7. PrintSpoofer
echo -e "${NC}[*] Download di PrintSpoofer64.exe...${RESET}"
curl -L -s -f "https://github.com/itm4n/PrintSpoofer/releases/latest/download/PrintSpoofer64.exe" -o "bin/windows/PrintSpoofer64.exe"
echo -e "${GREEN}[+] PrintSpoofer64 salvato in bin/windows/PrintSpoofer64.exe${RESET}"

# 8. GodPotato
echo -e "${NC}[*] Download di GodPotato-NET4.exe...${RESET}"
curl -L -s -f "https://github.com/BeichenDream/GodPotato/releases/download/V1.20/GodPotato-NET4.exe" -o "bin/windows/GodPotato-NET4.exe"
echo -e "${GREEN}[+] GodPotato-NET4.exe salvato in bin/windows/GodPotato-NET4.exe${RESET}"


echo -e "${GREEN}\n[+] Operazione completata! Tutti gli strumenti sono stati scaricati in 'bin/'.${RESET}"