import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper


app_key = '8vcak33a0tc5yw7'   # os los paso por was
app_secret = 'zuwgyplfgbb4mwx'
server_addr = "localhost"
server_port = 8070
redirect_uri = "http://" + server_addr + ":" + str(server_port)

class Dropbox:
    _access_token = ""
    _path = "/"
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        # por el puerto 8090 esta escuchando el servidor que generamos
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        # recibe la redireccio 302 del navegador
        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print (peticion)

        # buscar en solicitud el "auth_code"
        primera_linea =peticion.decode('UTF8').split('\n')[0]
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print ("\tauth_code: " + auth_code)

        # devolver una respuesta al usuario
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"
        client_connection.sendall(http_response.encode(encoding="utf-8"))
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        #############################################
        # RELLENAR CON CODIGO DE LAS PETICIONES HTTP
        # Y PROCESAMIENTO DE LAS RESPUESTAS HTTP
        # PARA LA OBTENCION DEL ACCESS TOKEN
        #############################################

        #1. Nabigatzailea zabaldu Dropbox-eko autorizazio URI-arekin
        params = {'response_type': 'code',
                  'client_id': app_key,
                  'redirect_uri': redirect_uri}
        params_encoded = urllib.parse.urlencode(params)
        uri = 'https://www.dropbox.com/oauth2/authorize?' + params_encoded
        webbrowser.open(uri)

        #2. auth_code-a lortu zerbitzari lokaletik
        auth_code = self.local_server()

        #3. auth_code-a aldatu access_token-agatik
        params = {'code': auth_code,
                  'grant_type': 'authorization_code',
                  'client_id': app_key,
                  'client_secret': app_secret,
                  'redirect_uri': redirect_uri}
        cabeceras = {'User-Agent': 'Python Client',
                     'Content-Type': 'application/x-www-form-urlencoded'}
        uri = 'https://api.dropboxapi.com/oauth2/token'
        respuesta = requests.post(uri, headers=cabeceras, data=params)
        print(respuesta.status_code)

        json_respuesta = json.loads(respuesta.content)
        self._access_token = json_respuesta['access_token']
        print("Access_Token: " + self._access_token)

        self._root.destroy()

    def list_folder(self, msg_listbox):
        print("/list_folder")
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-list_folder
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################

        path = "" if self._path == "/" else self._path.rstrip('/')

        datos = json.dumps({'path': path})
        cabeceras = { 'Authorization': 'Bearer ' + self._access_token,
                      'Content-Type': 'application/json'}
        respuesta = requests.post(uri, headers=cabeceras, data=datos)
        print("\tStatus: " + str(respuesta.status_code))
        print("\tRespuesta: " + respuesta.text)
        contenido_json = respuesta.json()

        self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)

    def transfer_file(self, file_path, file_data):
        print("/upload")
        uri = 'https://content.dropboxapi.com/2/files/upload'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-upload
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################

        dropbox_api_arg = json.dumps({
            'path': file_path,
            'mode': 'overwrite',
            'autorename': True,
            'mute': False
        })
        cabeceras = { 'Authorization': 'Bearer ' + self._access_token,
                      'Content-Type': 'application/octet-stream',
                      'Dropbox-API-Arg': dropbox_api_arg}
        respuesta = requests.post(uri, headers=cabeceras, data=file_data)
        print("\tStatus upload: " + str(respuesta.status_code))

    def delete_file(self, file_path):
        print("/delete_file")
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-delete
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################

        datos = json.dumps({'path': file_path})
        cabeceras = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }

        respuesta = requests.post(uri, headers=cabeceras, data=datos)
        print("\tStatus delete: " + str(respuesta.status_code))

    def create_folder(self, path):
        print("/create_folder")
       # https://www.dropbox.com/developers/documentation/http/documentation#files-create_folder
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################

        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
        datos = json.dumps({'path': path, 'autorename': False})
        cabeceras = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }

        respuesta = requests.post(uri, headers=cabeceras, data=datos)
        print("\tStatus create_folder: " + str(respuesta.status_code))

    ## Funcionalidad extra: renombrar archivos/carpetas
    def rename_file(self, old_path, new_path):
        print("/move_v2 (rename)")
        uri = 'https://api.dropboxapi.com/2/files/move_v2'

        datos = json.dumps({
            'from_path': old_path,
            'to_path': new_path,
            'allow_shared_folder': False,
            'autorename': False,
            'allow_ownership_transfer': False
        })

        cabeceras = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }

        respuesta = requests.post(uri, headers=cabeceras, data=datos)

        print("\tStatus rename: " + str(respuesta.status_code))
        print("\tRespuesta: " + respuesta.text)
