#Ikaslearen izen-abizenak: Uxue Aurtenetxe, Aimar Basterretxea, Ainhoa Tomas
#Irakasgaia eta taldea: Web Sistemak - 31. Taldea
#Entrega-data: 2026ko maiatzaren 15a
#Ataza kkonpilatu: Karpetan sartu -> python eGela.py <erabiltzailea> <'IZEN ABIZENA'>
import requests
import sys
import getpass
from bs4 import BeautifulSoup
import os
import csv


def main():
    # 1. Terminaletik parametroak jaso
    if len(sys.argv) < 3:
        print("Erabilera: python eGela_downloader.py <erabiltzailea> <'IZENA ABIZENA'>")
        sys.exit(1)

    username = sys.argv[1]
    full_name = sys.argv[2]
    password = getpass.getpass(f"Sartu {username} erabiltzailearen pasahitza: ")

    # --- 1. ESKAERA: GET Login orria ---
    url1 = "https://egela.ehu.eus/login/index.php"
    r1 = requests.get(url1, allow_redirects=False)

    print(f"\n1. ESKAERA: GET {url1}")
    print(f"1. ERANTZUNA: {r1.status_code} {r1.reason}")

    cookie_val = r1.headers.get('Set-Cookie').split(';')[0]
    soup1 = BeautifulSoup(r1.text, 'html.parser')
    logintoken = soup1.find('input', {'name': 'logintoken'})['value']

    # --- 2. ESKAERA: POST Login ---
    payload = {'username': username, 'password': password, 'logintoken': logintoken}
    headers = {'Cookie': cookie_val}
    r2 = requests.post(url1, data=payload, headers=headers, allow_redirects=False)

    print(f"\n2. ESKAERA: POST {url1}")
    print(f"2. ERANTZUNA: {r2.status_code} {r2.reason}")

    location2 = r2.headers.get('Location')
    if 'Set-Cookie' in r2.headers:
        cookie_val = r2.headers.get('Set-Cookie').split(';')[0]

    # --- 3. ESKAERA: GET Testsession ---
    headers = {'Cookie': cookie_val}
    r3 = requests.get(location2, headers=headers, allow_redirects=False)
    print(f"\n3. ESKAERA: GET {location2}")
    print(f"3. ERANTZUNA: {r3.status_code} {r3.reason}")

    location3 = r3.headers.get('Location')
    if 'Set-Cookie' in r3.headers:
        cookie_val = r3.headers.get('Set-Cookie').split(';')[0]

    # --- 4. ESKAERA: GET Profila (Egiaztapena) ---
    profile_url = "https://egela.ehu.eus/user/profile.php"
    headers = {'Cookie': cookie_val}
    r4 = requests.get(profile_url, headers=headers)

    if full_name.upper() in r4.text.upper():
        print(f"\nKautotzea ondo burutu da. Kaixo, {full_name}!")

        # --- 5. ESKAERA: Irakasgaiaren orria bilatu ---
        soup4 = BeautifulSoup(r4.text, 'html.parser')
        ikasgai_link = soup4.find('a', string=lambda t: t and "Web Sistemak" in t)
        if not ikasgai_link:
            ikasgai_link = soup4.find('a', {'title': lambda t: t and "Web Sistemak" in t})

        if ikasgai_link:
            websistemak_url = ikasgai_link['href']
            print(f"\n5. ESKAERA: GET {websistemak_url}")
            r5 = requests.get(websistemak_url, headers=headers)
            soup5 = BeautifulSoup(r5.text, 'html.parser')

            # --- 6. ATALA: Erlaitzak (Gaiak) identifikatu ---
            erlaitzak = soup5.find_all('a', class_=lambda x: x and ('nav-link' in x or 'nav-item' in x))
            gai_urleak = []
            print("\nIdentifikatutako gaiak (Erlaitzak):")
            for erlaitz in erlaitzak:
                izenburua = erlaitz.get_text(strip=True).replace("Nabarmenduta", "").strip()
                uri = erlaitz.get('href', '')
                if izenburua and "section=" in uri:
                    print(f"- {izenburua}: {uri}")
                    gai_urleak.append(uri)

            # --- 5. ATALA: PDF eta .py fitxategiak deskargatu ---
            print("\nFitxategiak bilatzen eta deskargatzen...")
            deskargatutakoak = set()
            for gai_url in gai_urleak:
                r_gai = requests.get(gai_url, headers=headers)
                soup_gai = BeautifulSoup(r_gai.text, 'html.parser')
                estekak = soup_gai.find_all('a', href=True)

                for esteka in estekak:
                    href = esteka.get('href', '')
                    testua = esteka.get_text(strip=True).lower()

                    if ("/mod/resource/" in href or "/pluginfile.php/" in href) and href not in deskargatutakoak:
                        r_file = requests.get(href, headers=headers, allow_redirects=True)

                        if 'Content-Disposition' in r_file.headers:
                            filename = r_file.headers['Content-Disposition'].split('filename=')[-1].replace('"', '')
                        else:
                            filename = r_file.url.split('/')[-1].split('?')[0]

                        filename = filename.split('.pdf')[0] + '.pdf' if '.pdf' in filename.lower() else filename
                        filename = filename.split('.py')[0] + '.py' if '.py' in filename.lower() else filename

                        if filename.lower().endswith(('.pdf', '.py')):
                            print(f"  -> Deskargatzen: {filename}")
                            with open(filename, 'wb') as f:
                                f.write(r_file.content)
                            deskargatutakoak.add(href)

            print("Deskarga guztiak amaitu dira.")

            # --- 6. ATALA: Zereginak bildu eta CSVan gorde ---
            csv_izena = "zereginak.csv"
            print(f"\nZereginak bilatzen eta '{csv_izena}' fitxategian gordetzen...")
            zereginen_zerrenda = []

            for gai_url in gai_urleak:
                r_gai = requests.get(gai_url, headers=headers)
                soup_gai = BeautifulSoup(r_gai.text, 'html.parser')
                zeregin_estekak = soup_gai.find_all('a', href=lambda x: x and "/mod/assign/view.php" in x)

                for z_esteka in zeregin_estekak:
                    url_zeregin = z_esteka['href']
                    if not any(z['Esteka'] == url_zeregin for z in zereginen_zerrenda):
                        izenburua = z_esteka.get_text(strip=True).replace("Zeregina", "").strip()
                        r_zeregin = requests.get(url_zeregin, headers=headers)
                        soup_zeregin = BeautifulSoup(r_zeregin.text, 'html.parser')

                        # Data bilatu
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