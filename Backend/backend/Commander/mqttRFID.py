from calendar import month

import paho.mqtt.client as mqtt
import os
import psycopg2
import datetime
import requests
import json
from threading import Timer


# pm2 start --interpreter ..\..\venv\Scripts\activate .\mqtt.py

#BASE_URL_OPERATIONS = 'http://127.0.0.1:8000/api/slock'
BASE_URL_OPERATIONS = 'https://slock.com.br/api/slock'
ENDPOINT_API_REDECASH = 'https://integrador.cashlocal.com.br/webhook/74cd9b5c-26ee-4d82-818a-a3060e3fc049'

topic_rfid = 'cashlocal/rfid/api/send'
topic_rfid_receiver = 'cashlocal/rfid/api/receiver'
topic_rfid_setup = 'cashlocal/rfid/api/setup'


# Define event callbacks
def on_connect(client, userdata, flags, rc):
    print("onConnect: " + str(rc))


def on_message(client, obj, msg):
    try:
        # Obtem a data e hora atuais
        now = datetime.datetime.now()
        formatted_date_time = now.strftime("%d/%m/%Y %H:%M:%S")

        # Converte o payload para uma string
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
        print(f'Payload in str: \n{payload_str}\n\n')  
        print(f'Dados Bruto da request: \n{data}\n\n')  
        
        print(f'Function: {data["function"]}\n')  
        print(f'Topico: {msg.topic}\n')  

        if msg.topic == topic_rfid:          
            if 'connected' in data["function"]:
                print("____________________________________")
                print("ESP32 -> Solicita atualizacao de data e hora")
                print("Topic: " + msg.topic)
                print("DataHora  : " + formatted_date_time)
                print("Mac  : " + data['mac'])
                print("____________________________________")

                day = str(now.strftime("%d"))
                month = str(now.strftime("%m"))
                year = str(now.strftime("%Y"))
                hour = str(now.strftime("%H"))
                minutes = str(now.strftime("%M"))
                seconds = str(now.strftime("%S"))

                packageMqtt = {
                    'mac': data['mac'],
                    'type': 'broadcast',
                    'function': 'set_time',
                    'day': day,
                    'month': month,
                    'full_year': year,
                    'hour': hour,
                    'minute': minutes,
                    'seconds': seconds
                }
                
                timer = Timer(20, publishFromThread, kwargs=packageMqtt)
                timer.start()
                print("Aguardando 20 segundos para executar a funcao...")
                

            if 'data' in data["function"]:                                
                
                headers = {'Content-Type': 'application/json'}

                # Converta o dicionário em uma string JSON usando UTF-8
                json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')

                # Envie a solicitação com os dados JSON codificados
                response = requests.post(ENDPOINT_API_REDECASH, headers=headers, data=json_data)

                # Verifica o status da resposta da API
                if response.status_code == 200:
                    print("Requisicao enviada com sucesso")
                else:
                    print(f"Falha ao enviar requisicao: {response.status_code}")
                    
                    
                packageMqtt = {
                    'mac': data['mac'],
                    'type': 'unicast',
                    'function': 'set_received_data'
                }
                
                mqttc.publish(topic_rfid_receiver, json.dumps(packageMqtt))
                print("Enviado ao uC que recebemos os dados")
                
            else:
                print('Nao tem funcao para esse comando')  
        else:
            print('Nao tem tratamento para este topico')                        
            
              
    except Exception as e:
        print('erro: ' + str(e))


def publishFromThread(**kwargs):

    print("Parametros recebidos na thread:")
    for key, value in kwargs.items():
        print(f"{key}: {value}")

    # Suponha que você queira publicar o JSON de volta ao MQTT
    mqttc.publish(topic_rfid_receiver, json.dumps(kwargs))
    print("Funcao a partir de thread executada.")
    

def on_publish(client, obj, mid):
    print("onPublish: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("onSubscribe: " + str(client))

def on_log(client, obj, level, string):
    print("onLog: {}".format(string))


mqttc = mqtt.Client()
# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

# Uncomment to enable debug messages
# mqttc.on_log = on_log



qtd_errors = 0

while True:
    print("WELCOME TO SERVER - OPERATIONS")
    data = datetime.datetime.now()
    # Connect
    mqttc.username_pw_set('AUTEN_SLOCKER', 'AUTEN_slocker@20052022')
    mqttc.connect('slock.com.br', 1883)

    # Start subscribe, with QoS level 0
    mqttc.subscribe(topic_rfid, 0)

    # Publish a message
    # mqttc.publish(topic, "my message")

    # Continue the network loop, exit when an error occurs
    rc = 0
    while rc == 0:
        rc = mqttc.loop()

    qtd_errors = qtd_errors + 1
    print("Data e Hora: " + str(data) + "rc: " + str(rc) + "Qtde Errors: " + str(qtd_errors))



