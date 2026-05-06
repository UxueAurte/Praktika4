#Ikaslearen izen-abizenak: Uxue Aurtenetxe, Aimar Basterretxea, Ainhoa Tomas
#Irakasgaia eta taldea: Web Sistemak - 31. Taldea
#Entrega-data: 2026ko maiatzaren 15a
#Ataza konpilatu: Karpetan sartu -> python eGela.py <erabiltzailea> <'IZEN ABIZENA'>
# -*- coding: UTF-8 -*-
from tkinter import messagebox
import requests
import urllib
from urllib.parse import unquote
from bs4 import BeautifulSoup
import time
import helper

class eGela:
    _login = 0
    _cookie = ""
    _curso = ""
    _refs = []
    _root = None
    _session = None

    def __init__(self, root):
        self._root = root

    def check_credentials(self, username, password, event=None):
        if hasattr(username, 'get'):
            username = username.get()
        if hasattr(password, 'get'):
            password = password.get()

        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        self._session = requests.Session()
        print("##### 1. PETICION #####")
        metodo = 'GET'
        uri = "https://egela.ehu.eus/login/index.php"
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        r1 = self._session.get(uri)
        print(f"1. ERANTZUNA: {r1.status_code} {r1.reason}")

        soup1 = BeautifulSoup(r1.text, 'html.parser')
        logintoken = soup1.find('input', {'name': 'logintoken'})['value']

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 2. PETICION #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        payload = {'username': username, 'password': password, 'logintoken': logintoken}
        r2 = self._session.post(uri, data=payload, allow_redirects=True)
        print(f"2. ERANTZUNA: {r2.status_code} {r2.reason}")

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 3. PETICION #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        profile_url = "https://egela.ehu.eus/user/profile.php"
        r3 = self._session.get(profile_url)
        print(f"3. ERANTZUNA: {r3.status_code} {r3.reason}")

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 4. PETICION #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        soup3 = BeautifulSoup(r3.text, 'html.parser')
        ikasgai_link = soup3.find('a', string=lambda t: t and "Web Sistemak" in t)
        if not ikasgai_link:
            ikasgai_link = soup3.find('a', {'title': lambda t: t and "Web Sistemak" in t})

        if ikasgai_link:
            websistemak_url = ikasgai_link['href']
            r4 = self._session.get(websistemak_url)
            print(f"4. ERANTZUNA: {r4.status_code} {r4.reason}")
        else:
            r4 = None

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        COMPROBACION_DE_LOG_IN = "profile.php" in r3.url and "login" not in r3.url

        if COMPROBACION_DE_LOG_IN:
            #############################################
            # ACTUALIZAR VARIABLES
            #############################################
            self._login = 1
            if ikasgai_link:
                self._curso = websistemak_url
            self._root.destroy()
        else:
            messagebox.showinfo("Alert Message", "Login incorrect!")

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("\n##### 4. PETICION (Página principal de la asignatura en eGela) #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        r5 = self._session.get(self._curso)
        print(f"ERANTZUNA: {r5.status_code} {r5.reason}")
        soup5 = BeautifulSoup(r5.text, 'html.parser')

        erlaitzak = soup5.find_all('a', class_=lambda x: x and ('nav-link' in x or 'nav-item' in x))
        gai_urleak = []
        for erlaitz in erlaitzak:
            uri = erlaitz.get('href', '')
            if "section=" in uri:
                gai_urleak.append(uri.split('#')[0])

        print("\n##### Analisis del HTML... #####")
        #############################################
        # ANALISIS DE LA PAGINA DEL AULA EN EGELA
        # PARA BUSCAR PDFs
        #############################################
        deskargatutakoak = set()
        recursos = []
        for gai_url in gai_urleak:
            r_gai = self._session.get(gai_url)
            soup_gai = BeautifulSoup(r_gai.text, 'html.parser')
            for esteka in soup_gai.find_all('a', href=True):
                href = esteka.get('href', '')
                if "/mod/resource/" in href and href not in deskargatutakoak:
                    deskargatutakoak.add(href)
                    recursos.append(href)

        # INICIALIZA Y ACTUALIZAR BARRA DE PROGRESO
        # POR CADA PDF ANIADIDO EN self._refs
        progress_step = float(100.0 / len(recursos)) if recursos else 100

        for href in recursos:
            r_resource = self._session.get(href, allow_redirects=True)
            final_url = r_resource.url
            content_type = r_resource.headers.get('Content-Type', '')

            if '/pluginfile.php/' in final_url and '.pdf' in final_url.lower():
                pdf_url = final_url
            elif 'application/pdf' in content_type:
                pdf_url = final_url
            else:
                soup_resource = BeautifulSoup(r_resource.text, 'html.parser')
                pdf_tag = soup_resource.find('a', href=lambda x: x and '/pluginfile.php/' in x)
                if not pdf_tag:
                    pdf_tag = soup_resource.find('object', data=lambda x: x and '/pluginfile.php/' in x)
                    if pdf_tag:
                        pdf_url = pdf_tag['data']
                    else:
                        progress += progress_step
                        progress_var.set(progress)
                        progress_bar.update()
                        continue
                else:
                    pdf_url = pdf_tag['href']

                if '.pdf' not in pdf_url.lower():
                    progress += progress_step
                    progress_var.set(progress)
                    progress_bar.update()
                    continue

            filename = unquote(pdf_url.split('/')[-1].split('?')[0])
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'

            self._refs.append({'pdf_name': filename, 'pdf_link': pdf_url})
            print(f"  PDF encontrado: {filename}")

            progress += progress_step
            progress_var.set(progress)
            progress_bar.update()
            time.sleep(0.1)

        popup.destroy()
        return self._refs

    def get_pdf(self, selection):

        print("\t##### descargando  PDF... #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        pdf_info = self._refs[selection]
        pdf_name = pdf_info['pdf_name']
        pdf_link = pdf_info['pdf_link']

        r = self._session.get(pdf_link, stream=True)
        pdf_content = r.content

        print(f"\tDescargado: {pdf_name}")
        return pdf_name, pdf_content