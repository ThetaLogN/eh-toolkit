#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== AUDIT AVANZATO CONTAINER HARDENING ===${NC}\n"

# 1. Verifica UID e User Namespace
echo -e "${YELLOW}[*] Verifica contesto Utente...${NC}"
if [ "$(id -u)" -eq 0 ]; then
    echo -e "${YELLOW}[!] Il container gira come ROOT interno.${NC}"
    # Controllo se siamo in un user namespace mappato
    if [ -f /proc/self/uid_map ]; then
        map_info=$(cat /proc/self/uid_map)
        if echo "$map_info" | grep -q "0          0"; then
            echo -e "${RED}[!] ATTENZIONE: User Namespace NON attivo. Il root del container è il root dell'host!${NC}"
        else
            echo -e "${GREEN}[+] User Namespace ATTIVO. Il root è mappato su un utente host non privilegiato.${NC}"
        fi
    fi
else
    echo -e "${GREEN}[+] Il container gira come utente non-root ($(whoami)). Sicurezza aumentata.${NC}"
fi

# 2. Controllo Spazi dei Nomi (Namespace) dell'Host
echo -e "\n${YELLOW}[*] Controllo isolamento Namespace dell'Host...${NC}"
# Controllo PID Namespace
host_pids=$(ps -ef 2>/dev/null | wc -l)
if [ "$host_pids" -gt 30 ]; then
    # Se vediamo molti processi e magari un init dell'host (systemd)
    if ps -ef 2>/dev/null | grep -q "systemd"; then
        echo -e "${RED}[!] PID Namespace CONDIVISO con l'host! Isolamento processi assente.${NC}"
    fi
else
    echo -e "${GREEN}[+] PID Namespace isolato correttamente.${NC}"
fi

# Controllo Network Namespace (Interfacce host visibili?)
if ip link 2>/dev/null | grep -q "docker0" || ip link 2>/dev/null | grep -q "eth0"; then
    # Verifica euristica semplice per capire se siamo in net=host
    if ip link 2>/dev/null | grep -q "lo" && ip link 2>/dev/null | grep -q "enp"; then
         echo -e "${RED}[!] Sospetta condivisione del Network Namespace dell'host.${NC}"
    fi
fi

# 3. Controllo Seccomp e AppArmor
echo -e "\n${YELLOW}[*] Controllo LSM (Linux Security Modules)...${NC}"
# AppArmor
if [ -f /sys/kernel/security/apparmor/profiles ]; then
    aa_status=$(cat /proc/self/attr/current 2>/dev/null)
    echo -e "Profilo AppArmor attuale: $aa_status"
    if [[ "$aa_status" == "unconfined" ]] || [[ -z "$aa_status" ]]; then
        echo -e "${RED}[!] AppArmor disattivato o 'unconfined' per questo container.${NC}"
    else
        echo -e "${GREEN}[+] AppArmor attivo: $aa_status${NC}"
    fi
fi

# Seccomp (0 = disabled, 1 = strict, 2 = filter)
if [ -f /proc/self/status ]; then
    seccomp_mode=$(grep "Seccomp:" /proc/self/status | awk '{print $2}')
    if [ "$seccomp_mode" == "2" ]; then
        echo -e "${GREEN}[+] Seccomp attivo (Modalità Filtro).${NC}"
    elif [ "$seccomp_mode" == "0" ]; then
        echo -e "${RED}[!] Seccomp DISATTIVATO! Il container può invocare qualsiasi syscall.${NC}"
    fi
fi

# 4. Analisi Mount Critici dell'Host
echo -e "\n${YELLOW}[*] Analisi approfondita dei Mount point sensibili...${NC}"
dangerous_mounts=("/etc/shadow" "/etc/cron.d" "/var/run/docker.sock" "/var/log" "/home")
for mnt in "${dangerous_mounts[@]}"; do
    if findmnt -n -o TARGET "$mnt" &>/dev/null || [ -e "$mnt" ]; then
        # Escludiamo i falsi positivi dei file interni del container
        if df "$mnt" 2>/dev/null | grep -q -E "overlay|shm"; then
            continue
        else
            echo -e "${RED}[!] File/Directory host esposta nel container: $mnt${NC}"
        fi
    fi
done

# Vecchi controlli (Privileged & Cap)
echo -e "\n${YELLOW}[*] Analisi Devices e Capabilities...${NC}"
if [ -b /dev/sda ] || [ -b /dev/nvme0n1 ]; then
    echo -e "${RED}[!] Accesso diretto ai dischi dell'host (/dev/sdX o nvme). Rischio breakout totale.${NC}"
fi

if command -v capsh &> /dev/null; then
    CAPS=$(capsh --print | grep "Current")
    for cap in "cap_sys_admin" "cap_sys_ptrace" "cap_sys_chroot" "cap_sys_module"; do
        if echo "$CAPS" | grep -q "$cap"; then
            echo -e "${RED}[!] Capability pericolosa attiva: $cap${NC}"
        fi
    done
fi

echo -e "\n${YELLOW}=== Fine dell'Audit Avanzato ===${NC}"
