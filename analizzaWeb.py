import argparse
import re
import sys
from bs4 import BeautifulSoup
import requests


def analizza_url(url):
    print(f"[*] Download della pagina: {url}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        risposta = requests.get(url, headers=headers, timeout=15)
        risposta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"\n[!] Errore durante il download del sito: {e}")
        sys.exit(1)

    html_content = risposta.text
    try:
        soup = BeautifulSoup(html_content, "lxml")
    except Exception:
        # Fallback se lxml non è installato
        soup = BeautifulSoup(html_content, "html.parser")

    # Estraiamo il testo pulito mantenendo gli spazi
    testo_visibile = soup.get_text(separator=" ")

    # --- 1. PROTOCOLLI ---
    pattern_protocolli = r"\b(https?|ftp|ssh|sftp|smb|rtsp):\/\/"
    urls_nel_sito = [a["href"] for a in soup.find_all(href=True)]
    protocolli_trovati = set(re.findall(pattern_protocolli, testo_visibile))
    for u in urls_nel_sito:
        match = re.search(pattern_protocolli, u)
        if match:
            protocolli_trovati.add(match.group(1))

    # --- 2. PROGRAMMI E VERSIONI (Es: FreePBX 16.0.40.7 o Apache/2.4.41) ---
    # Questo pattern cerca un nome (lettere/numeri) seguito opzionalmente da spazi,
    # "v", o una barra "/", e poi dal numero di versione (es. X.X.X)
    pattern_programmi_versioni = (
        r"\b([a-zA-Z0-9_\-]+)(?:\s+|/)(?:v(?:ersione|ersion)?\.?\s?)?(\d+\.\d+(?:\.\d+)*)\b"
    )

    # Cerchiamo sia nel testo visibile che nei meta tag / commenti utili
    versioni_trovate = set()
    matches = re.findall(pattern_programmi_versioni, testo_visibile, re.I)
    for programma, versione in matches:
        # Filtriamo parole comuni che potrebbero sembrare software ma non lo sono (es. "Anno 2026")
        if programma.lower() not in [
            "anno",
            "ore",
            "le",
            "i",
            "id",
            "aggiornato",
            "tel",
        ]:
            versioni_trovate.add(f"{programma} {versione}")

    # Controlliamo anche i meta tag "generator" (spesso usati da WordPress, Joomla, Drupal, ecc.)
    meta_generator = soup.find("meta", attrs={"name": "generator"})
    if meta_generator and meta_generator.get("content"):
        versioni_trovate.add(f"[Meta Generator] {meta_generator['content']}")

    # --- 3. NOMI UTENTE / MENZIONI ---
    pattern_username = r"@\w+"
    username_trovati = set(re.findall(pattern_username, testo_visibile))

    # --- 4. EMAIL E IP ---
    pattern_email = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    email_trovate = set(re.findall(pattern_email, testo_visibile))

    pattern_ip = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
    ip_trovati = set(re.findall(pattern_ip, testo_visibile))

    # --- STAMPA DEI RISULTATI ---
    print(f"\n================ ANALISI DI: {url} ================")

    print("\n[+] Protocolli rilevati nel testo o nei link:")
    print(
        ", ".join(protocolli_trovati).upper()
        if protocolli_trovati
        else "  Nessuno"
    )

    print("\n[+] Software e Versioni individuati:")
    if versioni_trovate:
        for pv in sorted(versioni_trovate):
            print(f"  - {pv}")
    else:
        print("  Nessun software/versione trovato evidente nell'HTML")

    print("\n[+] Nomi utente / Menzioni (@):")
    if username_trovati:
        for u in sorted(username_trovati):
            print(f"  - {u}")
    else:
        print("  Nessuno")

    print("\n[+] Altre informazioni utili:")
    print(
        f"  - Email trovate: {list(email_trovate) if email_trovate else 'Nessuna'}"
    )
    print(f"  - IP trovati: {list(ip_trovati) if ip_trovati else 'Nessuno'}")
    print("=" * (len(url) + 30))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scarica un HTML da un URL ed estrae informazioni utili, inclusi software e versioni."
    )
    parser.add_argument(
        "url",
        type=str,
        help="L'URL del sito web da analizzare (es. https://example.com)",
    )

    args = parser.parse_args()
    url_da_analizzare = args.url
    if not url_da_analizzare.startswith(("http://", "https://")):
        url_da_analizzare = "https://" + url_da_analizzare

    analizza_url(url_da_analizzare)
