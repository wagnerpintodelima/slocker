# -*- coding: utf-8 -*-

import requests

# pm2 start --interpreter ..\..\venv\Scripts\activate .\mqtt.py

ENDPOINT = 'https://slock.com.br/gestao/email/atendimento'

def send():        
    
    headers = {'Content-Type': 'application/json'}    

    # Envie a solicitação com os dados JSON codificados
    response = requests.get(ENDPOINT, headers=headers, data={})

    # Verifica o status da resposta da API
    if response.status_code == 200:
        print("Requisicao enviada com sucesso")        
        return True
    else:
        print("Falha ao enviar requisicao: {}".format(response.status_code))
        return False

def main():            
    send()
                        
if __name__ == "__main__":        
    try:
        main()
    finally:
        print('Encerrado')