import os
from http.server import SimpleHTTPRequestHandler
import socketserver
from urllib.parse import parse_qs, urlparse
import hashlib
from database import conect #importa a função para conectar no Banco de Dados

connection = conect()

class MyHandler(SimpleHTTPRequestHandler):
    def list_directory(self, path):
        try:
            f = open(os.path.join(path, 'home.html'), 'r', encoding='utf-8')
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f.read().encode('UTF-8'))
            f.close()
            return None
            
        except FileNotFoundError:
            pass

        return super().list_directory(path)
    
    #turmas
    def check_turma(self, codigo):
        cursor = connection.cursor()
        cursor.execute("SELECT id_turma FROM turmas WHERE id_turma = %s", (codigo,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            return True
        
        return False
    
    def adicionar_turma(self, codigo, descricao):
        cursor = connection.cursor()
        cursor.execute("INSERT INTO turmas (id_turma, descricao) VALUES (%s, %s)", (codigo, descricao))
        connection.commit()

        cursor.close()

    #atividades
    def check_atividade(self, codigo):
        cursor = connection.cursor()
        cursor.execute("SELECT id_atividade FROM atividades WHERE id_atividade = %s", (codigo,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            return True
        
        return False
    
    def adicionar_atividade(self, codigo, descricao):
        cursor = connection.cursor()
        cursor.execute("INSERT INTO atividades (id_atividade, descricao) VALUES (%s, %s)", (codigo, descricao))
        connection.commit()

        cursor.close()

    #check login teacher
    def check_teacher(self, user, password):
        cursor = connection.cursor()
        cursor.execute("SELECT senha FROM dados_login WHERE login = %s", (user,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return password_hash == result[0]
        
        return False
    
    #add teacher in database
    def add_teacher(self, user, password, name):
        cursor = connection.cursor()

        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        cursor.execute("INSERT INTO dados_login (login, senha, nome) VALUES (%s, %s, %s)", (user, password_hash, name))

        connection.commit()
        cursor.close()

    #verifica se existe professor para fazer a relação de professor com turma
    def check_prof_turma(self, user):
        #verifica se o user ja existe no arquivo
        cursor = connection.cursor()
        cursor.execute("SELECT id_professor FROM dados_login WHERE login = %s", (user,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            return True
        
        return False
    
    #verifica se ja existe um professor responsavel a turma que o usuario deseja relacionar
    def check_relacionamento(self, user, codigo):
        cursor = connection.cursor()
        # Obtendo o ID do usuário do professor pelo nome de usuário (login)
        cursor.execute("SELECT id_professor FROM dados_login WHERE login = %s", (user,))
        user_id = cursor.fetchone()

        # Verificando se o usuário com o nome de usuário fornecido existe
        if not user_id:
            cursor.close()
            return False  # Se o usuário não existir, retornar False

        # Verificando se existe um registro na tabela turmas_professor com o ID do usuário e o código da turma fornecidos
        cursor.execute("SELECT id_professor, id_turma FROM turmas_professor WHERE id_professor = %s AND id_turma = %s", (user_id[0], codigo))
        result = cursor.fetchone()
        cursor.close()

        if result:
            return True  
        else:
            return False  
    
    
    
    def add_turma_professor(self, user, codigo):
        #recupera o id do professor com base no nome de usuário fornecido
        cursor = connection.cursor()
        cursor.execute("SELECT id_professor FROM dados_login WHERE login = %s", (user,))
        result = cursor.fetchone()

        #verifica se o professor foi encontrado no banco de dados
        if result:
            id_professor = result[0] #extrai o id do professor com base no resultado da consulta
            cursor.close()

            #insere o registro na tabela turmas_professor com o id do professor recuperado
            cursor = connection.cursor()
            cursor.execute("INSERT INTO turmas_professor (id_professor, id_turma) VALUES (%s, %s)", (id_professor, codigo))
            connection.commit()
            cursor.close()

        else:
            #se o professor nao for encontrado
            with open(os.path.join(os.getcwd(), 'notEscolha.html'), 'r', encoding='UTF-8') as response_file:
                content = response_file.read()

            self.send_response(400)
            self.end_headers()
            self.wfile.write(content.encode('UTF-8'))
    
    def add_turma_atividade(self, codigoTurma, codigoAtividade):
        #recupera o id da turma com base no código fornecido
        cursor = connection.cursor()
        cursor.execute("SELECT id_turma FROM turmas WHERE id_turma = %s", (codigoTurma,))
        result = cursor.fetchone()

        #verifica se a turma foi encontrado no banco de dados
        if result:
            codigoTurma = result[0] #extrai o id da turma com base no resultado da consulta
            cursor.close()

            #insere o registro na tabela atividades_turma com o id da turma recuperado
            cursor = connection.cursor()
            cursor.execute("INSERT INTO atividades_turma (id_turma, id_atividade) VALUES (%s, %s)", (codigoTurma, codigoAtividade))
            connection.commit()
            cursor.close()

        else:
            #se a turma nao for encontrada
            with open(os.path.join(os.getcwd(), 'notEscolha.html'), 'r', encoding='UTF-8') as response_file:
                content = response_file.read()

            self.send_response(400)
            self.end_headers()
            self.wfile.write(content.encode('UTF-8'))

    def do_GET(self):
        """Serve a GET request."""
        #turmas
        if self.path == '/turmas':
            #tenta abrir o arquivo turmas.html
            try:
                with open(os.path.join(os.getcwd(), 'turmas.html'), 'r', encoding='UTF-8') as turmas_file:
                    content = turmas_file.read()
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode('UTF-8'))
                
            except FileNotFoundError:
                self.send_error(404, "File not found")

        elif self.path == '/turma_failed':
            #responde ao cliente com a mensagem de codigo ja existente
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            # le o conteudo da pagina login.html
            with open(os.path.join(os.getcwd(), 'notConfirm.html'), 'r', encoding='UTF-8') as turma_file:
                content = turma_file.read()

            #adiciona a mensagem de erro no conteudo da pagina
            self.wfile.write(content.encode('UTF-8'))

        #atividades
        elif self.path == '/atividades':
            #tenta abrir o arquivo atividades.html
            try:
                with open(os.path.join(os.getcwd(), 'atividades.html'), 'r', encoding='UTF-8') as atividades_file:
                    content = atividades_file.read()
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode('UTF-8'))
                
            except FileNotFoundError:
                self.send_error(404, "File not found")

        elif self.path == '/atividade_failed':
            #responde ao cliente com a mensagem de codigo ja existente
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            # le o conteudo da pagina login.html
            with open(os.path.join(os.getcwd(), 'notConfirm.html'), 'r', encoding='UTF-8') as atividade_file:
                content = atividade_file.read()

            #adiciona a mensagem de erro no conteudo da pagina
            self.wfile.write(content.encode('UTF-8'))
        
        elif self.path == '/login_failed':
            #responde ao professor com a mensagem de login/senha incorreta
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            # le o conteudo da pagina home.html
            with open(os.path.join(os.getcwd(), 'notRegister.html'), 'r', encoding='UTF-8') as login_file:
                content = login_file.read()

            #redireciona para a pagina de erro
            self.wfile.write(content.encode('UTF-8'))

        elif self.path.startswith('/cadastro'):
            #extraindo os parametros da url
            query_params = parse_qs(urlparse(self.path).query)
            user = query_params.get('user', [''])[0]
            senha = query_params.get('senha', [''])[0]

            #mensagem de boas-vindas
            welcome_message = f"Olá {user}, seja bem-vindo! Percebemos que você é novo por aqui. Faça seu cadastro!"

            #responde ao cliente com a pagina de cadastro
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            #le o conteudo da pagina cadastro.html
            with open(os.path.join(os.getcwd(), 'cadastro.html'), 'r', encoding='utf-8') as cadastro_file:
                content = cadastro_file.read()
            
            #substitui os marcadores de posição pelos valores correspondentes
            content = content.replace('{user}', user)
            content = content.replace('{senha}', senha)
            content = content.replace('{welcome_message}', welcome_message)

            #envia o conteudo modificado para o cliente
            self.wfile.write(content.encode('utf-8'))

            return #adicionando um return para evitar a execução do restante do código

        elif self.path.startswith('/escolha.html'):
            #obtendo as turmas do banco
            cursor = connection.cursor()
            cursor.execute("SELECT id_turma, descricao FROM turmas")
            results = cursor.fetchall() 
            cursor.close()

            #responde ao cliente com a pagina de cadastro
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            #le o conteudo da pagina cadastro.html
            with open(os.path.join(os.getcwd(), 'escolha.html'), 'r', encoding='utf-8') as file:
                content = file.read()

            #substitui os marcadores de posição pelos valores correspondentes            
            turmas = "<br>".join(f"{row[0]} - {row[1]}" for row in results)
            content = content.replace('{turmas}', turmas)

            #envia o conteudo modificado para o cliente
            self.wfile.write(content.encode('utf-8'))

            return #adicionando um return para evitar a execução do restante do código
        
        elif self.path.startswith('/atividades_turmas.html'):
            #TURMAS
            #obtendo as turmas do banco
            cursor = connection.cursor()
            cursor.execute("SELECT id_turma, descricao FROM turmas")
            turmas_results = cursor.fetchall() 
            cursor.close()

            #ATIVIDADES
            #obtendo as turmas do banco
            cursor = connection.cursor()
            cursor.execute("SELECT id_atividade, descricao FROM atividades")
            atividades_results = cursor.fetchall() 
            cursor.close()

            #responde ao cliente com a pagina de cadastro
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            #le o conteudo da pagina cadastro.html
            with open(os.path.join(os.getcwd(), 'atividades_turmas.html'), 'r', encoding='utf-8') as file:
                content = file.read()

            #substitui os marcadores de posição pelos valores correspondentes
            turmas_content = "<br>".join(f"{row[0]} - {row[1]}" for row in turmas_results)
            content = content.replace('{turmas}', turmas_content)

            atividades_content = "<br>".join(f"{row[0]} - {row[1]}" for row in atividades_results)
            content = content.replace('{atividades}', atividades_content)

            #envia o conteudo modificado para o cliente
            self.wfile.write(content.encode('utf-8'))

            return #adicionando um return para evitar a execução do restante do código
        
        elif self.path.startswith('/Notatividades_turmas.html'):
            #TURMAS
            #obtendo as turmas do banco
            cursor = connection.cursor()
            cursor.execute("SELECT id_turma, descricao FROM turmas")
            turmas_results = cursor.fetchall() 
            cursor.close()

            #ATIVIDADES
            #obtendo as turmas do banco
            cursor = connection.cursor()
            cursor.execute("SELECT id_atividade, descricao FROM atividades")
            atividades_results = cursor.fetchall() 
            cursor.close()

            #responde ao cliente com a pagina de cadastro
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            #le o conteudo da pagina cadastro.html
            with open(os.path.join(os.getcwd(), 'atividades_turmas.html'), 'r', encoding='utf-8') as file:
                content = file.read()

            #substitui os marcadores de posição pelos valores correspondentes
            turmas_content = "<br>".join(f"{row[0]} - {row[1]}" for row in turmas_results)
            content = content.replace('{turmas}', turmas_content)

            atividades_content = "<br>".join(f"{row[0]} - {row[1]}" for row in atividades_results)
            content = content.replace('{atividades}', atividades_content)

            #envia o conteudo modificado para o cliente
            self.wfile.write(content.encode('utf-8'))

            return #adicionando um return para evitar a execução do restante do código

        else:
            super().do_GET()


    def do_POST(self):
        if self.path == '/cad_turma':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('UTF-8')
            form_data = parse_qs(body, keep_blank_values=True)

            codigo = form_data.get("codigo", [''])[0]
            descricao = form_data.get("descricao", [''])[0]

            if self.check_turma(codigo) == True:
                self.send_response(302)
                self.send_header("Location", "/turma_failed")
                self.end_headers()
                return
            else:
                self.adicionar_turma(codigo, descricao)

                with open(os.path.join(os.getcwd(), 'confirm.html'), 'r', encoding='UTF-8') as response_file:
                    content = response_file.read()

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode('UTF-8'))
                return
        
        elif self.path == '/cad_atividade':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('UTF-8')
            form_data = parse_qs(body, keep_blank_values=True)

            codigo_atv = form_data.get("codigo_atv", [''])[0]
            descricao = form_data.get("descricao", [''])[0]

            if self.check_atividade(codigo_atv) == True:
                self.send_response(302)
                self.send_header("Location", "/atividade_failed")
                self.end_headers()
                return
            else:
                self.adicionar_atividade(codigo_atv, descricao)

                with open(os.path.join(os.getcwd(), 'confirm.html'), 'r', encoding='UTF-8') as response_file:
                    content = response_file.read()

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode('UTF-8'))
                return
        
        elif self.path == '/login_teacher':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('UTF-8')
            form_data = parse_qs(body,keep_blank_values=True)

            user = form_data.get("user", [''])[0]
            senha = form_data.get("senha", [''])[0]

            if(self.check_teacher(user, senha) == True):
                with open(os.path.join(os.getcwd(), 'links.html'), 'r', encoding='UTF-8') as response_file:
                    content = response_file.read()

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode('UTF-8'))
            
            else:
                #check if the user exist
                cursor = connection.cursor()
                cursor.execute("SELECT login FROM dados_login WHERE login = %s", (user,))
                result = cursor.fetchone()

                if result:
                    self.send_response(302)
                    self.send_header("Location", "/login_failed")
                    self.end_headers()
                    cursor.close()
                    return
                
                else:
                    self.send_response(302)
                    self.send_header("Location", f'/cadastro?login={user}&senha={senha}')
                    self.end_headers()
                    cursor.close()
                    return
        
        elif self.path.startswith('/confirm_register'):
            #obtém o comprimento do corpo da requisição
            content_length = int(self.headers['Content-Length'])
            #le o corpo da requisição
            body = self.rfile.read(content_length).decode('utf-8')
            #parseia os dados do formulário
            form_data = parse_qs(body, keep_blank_values=True)

            #query_params = parse_qs(urlparse(self.path).query)
            user = form_data.get('user', [''])[0]
            senha = form_data.get('senha', [''])[0]
            nome = form_data.get('nome', [''])[0]

            self.add_teacher(user, senha, nome)

            with open(os.path.join(os.getcwd(), 'links.html'), 'rb') as file:
                content = file.read().decode('utf-8')

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode('UTF-8'))

        elif self.path == '/escolha_turma':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('UTF-8')
            form_data = parse_qs(body,keep_blank_values=True)

            #query_params = parse_qs(urlparse(self.path).query)
            user_prof = form_data.get('user', [''])[0]
            codigo_turma = form_data.get('codigo', [''])[0]

            if self.check_prof_turma(user_prof) and self.check_turma(codigo_turma):
                if self.check_relacionamento(user_prof, codigo_turma) == False:

                    self.add_turma_professor(user_prof, codigo_turma)

                    with open(os.path.join(os.getcwd(), 'confirm.html'), 'r', encoding='UTF-8') as response_file:
                        content = response_file.read()

                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(content.encode('UTF-8'))

                else:
                    #le o conteudo da pagina
                    with open(os.path.join(os.getcwd(), 'notConfirm.html'), 'r', encoding='utf-8') as cadastro_file:
                        content = cadastro_file.read()

                    #responde ao cliente 
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(content.encode('utf-8'))

                    return #adicionando um return para evitar a execução do restante do código

            else:
                #se nao existir
                with open(os.path.join(os.getcwd(), 'notEscolha.html'), 'r', encoding='UTF-8') as response_file:
                    content = response_file.read()

                self.send_response(400)
                self.end_headers()
                self.wfile.write(content.encode('UTF-8'))

        elif self.path == '/escolha_atividade':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('UTF-8')
            form_data = parse_qs(body,keep_blank_values=True)

            #query_params = parse_qs(urlparse(self.path).query)
            codigo_turma = form_data.get('codigoTurma', [''])[0]
            codigo_atividade = form_data.get('codigoAtv', [''])[0]

            if self.check_turma(codigo_turma) and self.check_atividade(codigo_atividade):

                self.add_turma_atividade(codigo_turma, codigo_atividade)

                with open(os.path.join(os.getcwd(), 'confirm.html'), 'r', encoding='UTF-8') as response_file:
                    content = response_file.read()

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode('UTF-8'))

            else:
                #se nao existir
                with open(os.path.join(os.getcwd(), 'notatividades_turmas.html'), 'r', encoding='UTF-8') as response_file:
                    content = response_file.read()

                self.send_response(400)
                self.end_headers()
                self.wfile.write(content.encode('UTF-8'))

        else:
            SimpleHTTPRequestHandler.do_POST(self)


# IP e Porta utilizada
porta = 8000
ip = "0.0.0.0"

with socketserver.TCPServer((ip, porta), MyHandler) as httpd:
    print(f"Servidor iniciado no IP {ip}: {porta}")
    httpd.serve_forever()