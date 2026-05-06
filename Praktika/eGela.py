#Ikaslearen izen-abizenak: Uxue Aurtenetxe, Aimar Basterretxea, Ainhoa Tomas
#Irakasgaia eta taldea: Web Sistemak - 31. Taldea
#Entrega-data: 2026ko maiatzaren 15a
#Ataza konpilatu: Karpetan sartu -> python eGela.py <erabiltzailea> <'IZEN ABIZENA'>
import requests
import sys
import getpass
from bs4 import BeautifulSoup
import os
import csv
import urllib.parse


def main():
    # 1. Terminaletik parametroak jaso
    if len(sys.argv) < 3:
        print("Erabilera: python eGela_downloader.py <erabiltzailea> <'IZENA ABIZENA'>")
        sys.exit(1)

    username = sys.argv[1]
    full_name = sys.argv[2]
    password = getpass.getpass(f"Sartu {username} erabiltzailearen pasahitza: ")

    session = requests.Session()

    # --- 1. ESKAERA: GET Login orria ---
    url1 = "https://egela.ehu.eus/login/index.php"
    r1 = session.get(url1)
    print(f"\n1. ESKAERA: GET {url1}")
    print(f"1. ERANTZUNA: {r1.status_code} {r1.reason}")

    soup1 = BeautifulSoup(r1.text, 'html.parser')
    logintoken = soup1.find('input', {'name': 'logintoken'})['value']

    # --- 2. ESKAERA: POST Login ---
    payload = {'username': username, 'password': password, 'logintoken': logintoken}
    r2 = session.post(url1, data=payload, allow_redirects=True)
    print(f"\n2. ESKAERA: POST {url1}")
    print(f"2. ERANTZUNA: {r2.status_code} {r2.reason}")

    # --- 3. ESKAERA: GET Profila (Egiaztapena) ---
    profile_url = "https://egela.ehu.eus/user/profile.php"
    r4 = session.get(profile_url)

    if full_name.upper() in r4.text.upper():
        print(f"\nKautotzea ondo burutu da. Kaixo, {full_name}!")

        # --- Web Sistemak irakasgaia bilatu ---
        soup4 = BeautifulSoup(r4.text, 'html.parser')
        ikasgai_link = soup4.find('a', string=lambda t: t and "Web Sistemak" in t)
        if not ikasgai_link:
            ikasgai_link = soup4.find('a', {'title': lambda t: t and "Web Sistemak" in t})

        if ikasgai_link:
            websistemak_url = ikasgai_link['href']
            print(f"\n5. ESKAERA: GET {websistemak_url}")
            r5 = session.get(websistemak_url)
            soup5 = BeautifulSoup(r5.text, 'html.parser')

            # --- Erlaitzak (Gaiak) identifikatu ---
            erlaitzak = soup5.find_all('a', class_=lambda x: x and ('nav-link' in x or 'nav-item' in x))
            gai_urleak = []
            print("\nIdentifikatutako gaiak (Erlaitzak):")
            for erlaitz in erlaitzak:
                izenburua = erlaitz.get_text(strip=True).replace("Nabarmenduta", "").strip()
                uri = erlaitz.get('href', '')
                if izenburua and "section=" in uri:
                    print(f"- {izenburua}: {uri}")
                    gai_urleak.append(uri.split('#')[0])  # Kendu #tabs-tree-start

            # --- 5. ATALA: PDF fitxategiak listatu ---
            print(f"\nPDF fitxategiak bilatzen...")
            deskargatutakoak = set()
            pdf_lista = []

            for gai_url in gai_urleak:
                r_gai = session.get(gai_url)
                soup_gai = BeautifulSoup(r_gai.text, 'html.parser')
                estekak = soup_gai.find_all('a', href=True)

                for esteka in estekak:
                    href = esteka.get('href', '')
                    if "/mod/resource/" in href and href not in deskargatutakoak:
                        deskargatutakoak.add(href)

                        r_resource = session.get(href, allow_redirects=True)
                        final_url = r_resource.url
                        content_type = r_resource.headers.get('Content-Type', '')

                        # Moodle-k zuzenean PDF-ra birbidaltzen du normalean
                        if '/pluginfile.php/' in final_url and '.pdf' in final_url.lower():
                            pdf_url = final_url
                        elif 'application/pdf' in content_type:
                            pdf_url = final_url
                        else:
                            # HTML orrian bilatu pluginfile esteka
                            soup_resource = BeautifulSoup(r_resource.text, 'html.parser')
                            pdf_tag = soup_resource.find('a', href=lambda x: x and '/pluginfile.php/' in x)
                            if not pdf_tag:
                                pdf_tag = soup_resource.find('object', data=lambda x: x and '/pluginfile.php/' in x)
                                if pdf_tag:
                                    pdf_url = pdf_tag['data']
                                else:
                                    continue
                            else:
                                pdf_url = pdf_tag['href']

                            if '.pdf' not in pdf_url.lower():
                                continue

                        filename = urllib.parse.unquote(pdf_url.split('/')[-1].split('?')[0])
                        if not filename.lower().endswith('.pdf'):
                            filename += '.pdf'
                        pdf_lista.append({'pdf_name': filename, 'pdf_link': pdf_url})

            print(f"\nAurkitutako PDFak ({len(pdf_lista)}):")
            for i, pdf in enumerate(pdf_lista):
                print(f"  {i}. {pdf['pdf_name']}")
                print(f"     {pdf['pdf_link']}")

            # --- PDF fitxategiak deskargatu ---
            deskarga_karpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deskargak")
            os.makedirs(deskarga_karpeta, exist_ok=True)
            print(f"\nPDFak deskargatzen '{deskarga_karpeta}' karpetara...")

            for pdf in pdf_lista:
                dest_path = os.path.join(deskarga_karpeta, pdf['pdf_name'])
                r_pdf = session.get(pdf['pdf_link'], stream=True)
                with open(dest_path, 'wb') as f_pdf:
                    for chunk in r_pdf.iter_content(chunk_size=8192):
                        f_pdf.write(chunk)
                print(f"  -> Deskargatuta: {pdf['pdf_name']}")

            # --- 6. ATALA: Zereginak bildu eta CSVan gorde ---
            csv_izena = "zereginak.csv"
            print(f"\nZereginak bilatzen eta '{csv_izena}' fitxategian gordetzen...")
            zereginen_zerrenda = []

            for gai_url in gai_urleak:
                r_gai = session.get(gai_url)
                soup_gai = BeautifulSoup(r_gai.text, 'html.parser')
                zeregin_estekak = soup_gai.find_all('a', href=lambda x: x and "/mod/assign/view.php" in x)

                for z_esteka in zeregin_estekak:
                    url_zeregin = z_esteka['href']
                    if not any(z['Esteka'] == url_zeregin for z in zereginen_zerrenda):
                        izenburua = z_esteka.get_text(strip=True).replace("Zeregina", "").strip()
                        r_zeregin = session.get(url_zeregin)
                        soup_zeregin = BeautifulSoup(r_zeregin.text, 'html.parser')

                        data_el = soup_zeregin.find('td', class_='cell c1 lastcol')
                        if not data_el:
                            data_testua = soup_zeregin.find(string=lambda t: t and ("Epemuga" in t or "Due date" in t))
                            if data_testua: data_el = data_testua.find_next()

                        entrega_data = data_el.get_text(strip=True) if data_el else "Ez dago datarik"
                        zereginen_zerrenda.append({
                            'Izenburua': izenburua,
                            'Data': entrega_data,
                            'Esteka': url_zeregin
                        })
                        print(f"  -> Aurkituta: {izenburua}")

            with open(csv_izena, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Izenburua', 'Data', 'Esteka'])
                writer.writeheader()
                writer.writerows(zereginen_zerrenda)

            print(f"Zeregin guztiak '{csv_izena}' fitxategian gorde dira.")
            print(f"Lan-direktorioa: {os.getcwd()}")
        else:
            print("\nEzin izan da 'Web Sistemak' irakasgaia aurkitu.")

        input("\nSakatu ENTER programa amaitzeko...")
    else:
        print("\nKautotzeak huts egin du. Izena ez dago profilean.")
        sys.exit(1)


if __name__ == "__main__":
    main()