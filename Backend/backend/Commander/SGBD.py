import sqlite3

class BD():            
    
    def __init__(self, banco_de_dados=fr'D:\Projetos\db.sqlite3'):
        """
        Inicializa a classe e estabelece a conexão com o banco de dados.
        """
        self.banco_de_dados = banco_de_dados
        self.conn = sqlite3.connect(self.banco_de_dados)        
        self.cursor = self.conn.cursor()


    def select(self, query, is_fetch_one=False):        
        """
        Executa uma consulta SELECT e retorna os resultados.
        """
        self.cursor.execute(query)
        
        columns = [desc[0] for desc in self.cursor.description]  # Obtem os nomes das colunas
        if is_fetch_one:
            row = self.cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        rows = self.cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]

    def execute(self, query):
        """
        Executa uma consulta sem retorno, como INSERT, UPDATE, DELETE.
        """
        self.cursor.execute(query)
        self.conn.commit()
    
    def close(self):
        """
        Fecha a conexão com o banco de dados.
        """
        self.conn.close()