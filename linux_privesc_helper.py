#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import argparse

# Lista di binari GTFOBins noti che possono essere usati per privesc se hanno SUID
GTFO_BINARIES = {
    'bash', 'sh', 'dash', 'ash', 'zsh', 'python', 'python3', 'perl', 'ruby',
    'lua', 'php', 'nmap', 'systemctl', 'find', 'vim', 'nano', 'git', 'awk',
    'sed', 'grep', 'env', 'xargs', 'tar', 'zip', 'unzip', 'base64', 'cat',
    'curl', 'wget', 'docker', 'socat', 'nc', 'netcat', 'od', 'less', 'more',
    'tcpdump', 'dd', 'cp', 'mv', 'ln', 'chown', 'chmod', 'pkexec', 'make',
    'apt', 'apt-get', 'yum', 'pip', 'node', 'npm', 'scp', 'sftp', 'ftp', 'tftp'
}


def print_section(title):
    print("\n" + "=" * 70)
    print(f"[*] {title}")
    print("=" * 70)


def check_system_info():
    print_section("INFORMAZIONI DI SISTEMA")
    
    # OS Release
    if os.path.exists('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('PRETTY_NAME='):
                    name = line.strip().split('=')[1].replace('"', '')
                    print(f"[+] OS: {name}")
                    break
    else:
        print(f"[+] OS: {sys.platform}")

    # Kernel version
    try:
        kernel = subprocess.check_output(['uname', '-a'], text=True).strip()
        print(f"[+] Kernel: {kernel}")
    except Exception:
        print("[-] Kernel: Impossibile determinare")


def check_user_info():
    print_section("INFORMAZIONI UTENTE E GRUPPI")
    try:
        uid = os.getuid()
        gid = os.getgid()
        import pwd
        import grp
        user_name = pwd.getpwuid(uid).pw_name
        group_name = grp.getgrgid(gid).gr_name
        print(f"[+] Utente corrente: {user_name} (UID: {uid})")
        print(f"[+] Gruppo primario: {group_name} (GID: {gid})")
        
        # Gruppi secondari
        groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
        print(f"[+] Gruppi secondari: {', '.join(groups)}")
        
        # Evidenzia gruppi sensibili
        dangerous_groups = {'sudo', 'wheel', 'docker', 'lxd', 'lxc', 'shadow', 'disk', 'adm'}
        found_dangerous = dangerous_groups.intersection(set(groups))
        if found_dangerous:
            print(f"[!] ATTENZIONE: Fai parte di gruppi sensibili: {', '.join(found_dangerous)}")
            if 'docker' in found_dangerous:
                print("    -> Docker: Puoi elevare i privilegi avviando un container root con volume host mappato.")
            if 'lxd' in found_dangerous or 'lxc' in found_dangerous:
                print("    -> LXD/LXC: Puoi elevare i privilegi creando un container privilegiato.")
            if 'shadow' in found_dangerous:
                print("    -> Shadow: Puoi leggere direttamente il file /etc/shadow.")
            if 'disk' in found_dangerous:
                print("    -> Disk: Hai accesso in lettura/scrittura grezzo ai dischi di sistema.")
    except Exception as e:
        print(f"[-] Errore nel recupero info utente: {e}")


def check_sudo_capabilities():
    print_section("PRIVILEGI SUDO (NON INTERATTIVO)")
    try:
        proc = subprocess.run(['sudo', '-n', '-l'], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            print("[+] Configurazione Sudo (sudo -n -l):")
            print(proc.stdout.strip())
        else:
            print("[-] Sudo richiede una password per elencare i privilegi o l'utente non ha privilegi sudo.")
    except Exception as e:
        print(f"[-] Impossibile eseguire sudo -l: {e}")


def check_suid_sgid():
    print_section("FILE SUID E SGID")
    # Cartelle comuni da scansionare per evitare scansioni di rete lente
    scan_dirs = ['/bin', '/usr/bin', '/sbin', '/usr/sbin', '/usr/local/bin', '/usr/local/sbin', '/opt']
    
    suid_files = []
    sgid_files = []

    print("[*] Ricerca in corso in cartelle di sistema...")
    for s_dir in scan_dirs:
        if not os.path.exists(s_dir):
            continue
        for root, _, files in os.walk(s_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Saltiamo i link simbolici
                    if os.path.islink(file_path):
                        continue
                    stat = os.stat(file_path)
                    # SUID check
                    if (stat.st_mode & 0o4000) != 0:
                        suid_files.append(file_path)
                    # SGID check
                    if (stat.st_mode & 0o2000) != 0:
                        sgid_files.append(file_path)
                except Exception:
                    pass

    if suid_files:
        print(f"\n[+] Trovati {len(suid_files)} file SUID:")
        for path in sorted(suid_files):
            name = os.path.basename(path)
            if name.lower() in GTFO_BINARIES:
                print(f"  [!] {path} <-- ATTENZIONE: Presente su GTFOBins!")
            else:
                print(f"  - {path}")
    else:
        print("[-] Nessun file SUID trovato nelle cartelle scansionate.")

    if sgid_files:
        print(f"\n[+] Trovati {len(sgid_files)} file SGID:")
        for path in sorted(sgid_files):
            print(f"  - {path}")


def check_writable_files():
    print_section("FILE DI SISTEMA SCRIVIBILI")
    critical_files = [
        '/etc/passwd',
        '/etc/shadow',
        '/etc/sudoers',
        '/etc/exports',
        '/etc/crontab',
        '/etc/hosts',
        '/etc/resolv.conf'
    ]
    
    found_writable = False
    for path in critical_files:
        if os.path.exists(path):
            if os.access(path, os.W_OK):
                print(f"  [!] SCRIVIBILE: {path}")
                found_writable = True
            else:
                # Controlliamo se la directory padre è scrivibile (permette di sostituire il file)
                parent_dir = os.path.dirname(path)
                if os.access(parent_dir, os.W_OK):
                    print(f"  [!] CARTELLA PADRE SCRIVIBILE: {path} (può essere rimosso e sostituito!)")
                    found_writable = True

    if not found_writable:
        print("[-] Nessun file di sistema critico è scrivibile dall'utente corrente.")


def extract_commands_paths(command_line):
    """Estrae i potenziali percorsi assoluti di eseguibili/script da una riga di comando cron."""
    # Trova stringhe che iniziano con '/' e contengono caratteri validi per percorsi
    paths = re.findall(r'(/[a-zA-Z0-9_\-\./]+)', command_line)
    valid_paths = []
    for p in paths:
        # Pulisce eventuali caratteri residui a fine stringa e filtra directory vuote o banali
        clean_path = p.rstrip('.')
        if os.path.exists(clean_path) and os.path.isfile(clean_path):
            valid_paths.append(clean_path)
    return list(set(valid_paths))


def check_cronjobs():
    print_section("ANALISI CRONJOB E PERMESSI")
    cron_files = []
    
    if os.path.exists('/etc/crontab'):
        cron_files.append('/etc/crontab')
        
    cron_d = '/etc/cron.d'
    if os.path.exists(cron_d) and os.path.isdir(cron_d):
        try:
            for file in os.listdir(cron_d):
                cron_files.append(os.path.join(cron_d, file))
        except Exception:
            pass

    found_cron_vuln = False

    for file_path in cron_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                header_printed = False
                for line_num, line in enumerate(f, 1):
                    clean_line = line.strip()
                    # Salta commenti e righe vuote
                    if not clean_line or clean_line.startswith('#'):
                        continue
                    
                    # Cerca percorsi assoluti nel comando
                    paths = extract_commands_paths(clean_line)
                    for path in paths:
                        # Controlliamo se il file o la sua cartella padre sono scrivibili
                        is_file_writable = os.access(path, os.W_OK)
                        parent_dir = os.path.dirname(path)
                        is_dir_writable = os.access(parent_dir, os.W_OK)

                        if is_file_writable or is_dir_writable:
                            if not header_printed:
                                print(f"\n[*] File cron: {file_path}")
                                header_printed = True
                            
                            status = "SCRIVIBILE" if is_file_writable else "CARTELLA PADRE SCRIVIBILE"
                            print(f"  [!] Linea {line_num}: {clean_line[:80]}")
                            print(f"      -> Eseguibile: {path} ({status})")
                            found_cron_vuln = True
        except Exception as e:
            print(f"[-] Impossibile leggere {file_path}: {e}")

    if not found_cron_vuln:
        print("[-] Nessun eseguibile richiamato nei cronjob di sistema è risultato modificabile.")


def decode_tcp_hex(hex_str):
    """Decodifica IP e Porta dal formato esadecimale di /proc/net/tcp."""
    try:
        hex_ip, hex_port = hex_str.split(':')
        # Little-endian IP conversion
        ip_bytes = [int(hex_ip[i:i+2], 16) for i in range(6, -1, -2)]
        ip = ".".join(map(str, ip_bytes))
        port = int(hex_port, 16)
        return ip, port
    except Exception:
        return None


def check_local_ports():
    print_section("SERVIZI E PORTE IN ASCOLTO (LOCALI)")
    
    tcp_file = '/proc/net/tcp'
    if not os.path.exists(tcp_file):
        print("[-] File /proc/net/tcp non presente (sistema non Linux o procfs non montato).")
        return

    listeners = []
    try:
        with open(tcp_file, 'r') as f:
            # Salta intestazione
            next(f)
            for line in f:
                parts = line.split()
                if len(parts) >= 4:
                    local_address = parts[1]
                    state = parts[3]
                    # Stato '0A' indica LISTEN in TCP
                    if state == '0A':
                        decoded = decode_tcp_hex(local_address)
                        if decoded:
                            listeners.append(decoded)
    except Exception as e:
        print(f"[-] Errore durante la lettura di /proc/net/tcp: {e}")

    if listeners:
        print("[+] Porte TCP in stato LISTEN rilevate:")
        for ip, port in sorted(set(listeners)):
            highlight = ""
            # Evidenzia servizi in ascolto solo in locale (127.0.0.1)
            if ip.startswith('127.'):
                highlight = " <-- Rilevabile solo in locale (potenziale vettore di Pivoting/Privesc)"
            print(f"  - {ip}:{port}{highlight}")
    else:
        print("[-] Nessuna porta TCP LISTEN decodificata.")


def main():
    parser = argparse.ArgumentParser(
        description="Esegue una scansione locale di configurazioni del sistema Linux alla ricerca di potenziali vettori di privilege escalation."
    )
    # Nessun parametro richiesto per default, ma permette espansione
    parser.parse_args()

    print("[*] Avvio scansione locale Privilege Escalation...")
    check_system_info()
    check_user_info()
    check_sudo_capabilities()
    check_writable_files()
    check_cronjobs()
    check_local_ports()
    print("\n[*] Analisi completata.")


if __name__ == "__main__":
    main()
