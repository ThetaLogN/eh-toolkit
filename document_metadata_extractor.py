import os
import sys
import csv
import json
import zipfile
import xml.etree.ElementTree as ET
import argparse

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def find_tag_agnostic(root, tag_name):
    """Trova un elemento XML ignorando i namespace."""
    for elem in root.iter():
        local_name = elem.tag.split('}')[-1]
        if local_name == tag_name:
            return elem
    return None


def extract_office_metadata(file_path):
    """Estrae i metadati da file Office (Docx, Xlsx, Pptx) leggendo l'archivio zip."""
    meta = {
        'Creator': None,
        'LastModifiedBy': None,
        'Created': None,
        'Modified': None,
        'Revision': None,
        'Application': None,
        'Company': None
    }

    try:
        with zipfile.ZipFile(file_path) as z:
            # Parsing dei metadati principali
            if 'docProps/core.xml' in z.namelist():
                core_xml = z.read('docProps/core.xml')
                root = ET.fromstring(core_xml)

                def get_val(tag):
                    elem = find_tag_agnostic(root, tag)
                    return elem.text.strip() if elem is not None and elem.text else None

                meta['Creator'] = get_val('creator')
                meta['LastModifiedBy'] = get_val('lastModifiedBy')
                meta['Created'] = get_val('created')
                meta['Modified'] = get_val('modified')
                meta['Revision'] = get_val('revision')

            # Parsing dell'applicazione creatrice e azienda
            if 'docProps/app.xml' in z.namelist():
                app_xml = z.read('docProps/app.xml')
                root = ET.fromstring(app_xml)

                def get_val(tag):
                    elem = find_tag_agnostic(root, tag)
                    return elem.text.strip() if elem is not None and elem.text else None

                meta['Application'] = get_val('Application')
                meta['Company'] = get_val('Company')

        return meta
    except Exception as e:
        return {'Error': f"Errore durante il parsing del file Office: {e}"}


def extract_pdf_metadata(file_path):
    """Estrae i metadati da un file PDF usando pypdf."""
    if not HAS_PYPDF:
        return {'Warning': "Libreria 'pypdf' non installata. Saltato il parsing del PDF."}

    meta = {
        'Creator': None,
        'LastModifiedBy': None,
        'Created': None,
        'Modified': None,
        'Revision': None,
        'Application': None,
        'Company': None
    }

    try:
        reader = PdfReader(file_path)
        pdf_meta = reader.metadata
        if pdf_meta:
            meta['Creator'] = pdf_meta.author if pdf_meta.author else None
            meta['Application'] = pdf_meta.creator if pdf_meta.creator else None

            if pdf_meta.producer and not meta['Application']:
                meta['Application'] = pdf_meta.producer

            # Date format in PDF: D:YYYYMMDDHHmmSSOHH'mm'
            created = pdf_meta.get('/CreationDate')
            modified = pdf_meta.get('/ModDate')

            # Puliamo leggermente il formato data
            if created and created.startswith('D:'):
                created = created[2:]
            if modified and modified.startswith('D:'):
                modified = modified[2:]

            meta['Created'] = created
            meta['Modified'] = modified

        return meta
    except Exception as e:
        return {'Error': f"Errore durante il parsing del file PDF: {e}"}


def scan_path(target_path):
    """Scansiona ricorsivamente una cartella o elabora un singolo file cercandone i metadati."""
    supported_extensions = ('.pdf', '.docx', '.xlsx', '.pptx')
    results = []

    if os.path.isfile(target_path):
        if target_path.lower().endswith(supported_extensions):
            results.append((target_path, target_path.split('.')[-1].lower()))
    elif os.path.isdir(target_path):
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.lower().endswith(supported_extensions):
                    file_path = os.path.join(root, file)
                    results.append((file_path, file.split('.')[-1].lower()))

    metadata_records = []
    pdf_skipped_warning = False

    for file_path, ext in results:
        if ext == 'pdf':
            if not HAS_PYPDF:
                pdf_skipped_warning = True
                continue
            meta = extract_pdf_metadata(file_path)
        else:
            meta = extract_office_metadata(file_path)

        # Aggiungiamo i dati di base del file
        record = {
            'FilePath': file_path,
            'FileName': os.path.basename(file_path),
            'Extension': ext,
            'Creator': meta.get('Creator'),
            'LastModifiedBy': meta.get('LastModifiedBy'),
            'Created': meta.get('Created'),
            'Modified': meta.get('Modified'),
            'Revision': meta.get('Revision'),
            'Application': meta.get('Application'),
            'Company': meta.get('Company'),
            'Status': 'OK'
        }

        if 'Error' in meta:
            record['Status'] = 'Error'
            record['ErrorDetail'] = meta['Error']

        metadata_records.append(record)

    if pdf_skipped_warning:
        print("[!] Nota: Alcuni file PDF sono stati ignorati perché la libreria 'pypdf' non è installata.")

    return metadata_records


def main():
    parser = argparse.ArgumentParser(
        description="Scansiona file PDF e Office (.docx, .xlsx, .pptx) per estrarre metadati e identificare autori, aziende e software utilizzati."
    )
    parser.add_argument(
        "target_path",
        help="Il file o la cartella da scansionare ricorsivamente"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Salva i risultati in un file. Usa l'estensione .csv o .json per decidere il formato di output."
    )

    args = parser.parse_args()

    if not os.path.exists(args.target_path):
        print(f"[-] Errore: Il percorso '{args.target_path}' non esiste!")
        sys.exit(1)

    print(f"[*] Avvio estrazione metadati su: {args.target_path}...")
    records = scan_path(args.target_path)
    print(f"[+] Trovati {len(records)} file validi analizzati.")
    print("=" * 70)

    # Stampiamo a schermo una sintesi
    for rec in records:
        print(f"File: {rec['FilePath']}")
        if rec['Status'] == 'Error':
            print(f"  [!] Errore di lettura: {rec.get('ErrorDetail')}")
        else:
            print(f"  - Autore/Creatore:  {rec['Creator'] if rec['Creator'] else 'N/D'}")
            print(f"  - Ultima Modifica Da: {rec['LastModifiedBy'] if rec['LastModifiedBy'] else 'N/D'}")
            print(f"  - Data Creazione:   {rec['Created'] if rec['Created'] else 'N/D'}")
            print(f"  - Data Modifica:    {rec['Modified'] if rec['Modified'] else 'N/D'}")
            print(f"  - Software/App:     {rec['Application'] if rec['Application'] else 'N/D'}")
            print(f"  - Azienda/Org:      {rec['Company'] if rec['Company'] else 'N/D'}")
            if rec['Revision']:
                print(f"  - Revisione:        {rec['Revision']}")
        print("-" * 50)

    # Scrittura su file se richiesto
    if args.output and records:
        ext = args.output.split('.')[-1].lower()
        try:
            if ext == 'json':
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(records, f, indent=4, ensure_ascii=False)
                print(f"[+] Risultati salvati correttamente in JSON: {args.output}")
            elif ext == 'csv':
                # Prepariamo le intestazioni basate sulle chiavi comuni dei record
                headers = ['FilePath', 'FileName', 'Extension', 'Creator', 'LastModifiedBy', 'Created', 'Modified', 'Revision', 'Application', 'Company', 'Status']
                with open(args.output, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                    writer.writeheader()
                    for rec in records:
                        writer.writerow(rec)
                print(f"[+] Risultati salvati correttamente in CSV: {args.output}")
            else:
                # Output di testo generico
                with open(args.output, 'w', encoding='utf-8') as f:
                    for rec in records:
                        f.write(f"File: {rec['FilePath']}\n")
                        f.write(f"  Autore:  {rec['Creator']}\n")
                        f.write(f"  Modificato da: {rec['LastModifiedBy']}\n")
                        f.write(f"  Creato:   {rec['Created']}\n")
                        f.write(f"  Modificato:    {rec['Modified']}\n")
                        f.write(f"  Software: {rec['Application']}\n")
                        f.write(f"  Azienda:  {rec['Company']}\n")
                        f.write("-" * 50 + "\n")
                print(f"[+] Risultati salvati correttamente come testo: {args.output}")
        except Exception as e:
            print(f"[-] Errore durante il salvataggio dei dati: {e}")


if __name__ == "__main__":
    main()
