from calendar import month
import time
import paho.mqtt.client as mqtt
import os
import psycopg2
import datetime
import requests
import json
from threading import Timer
from twilio.rest import Client
import re



# pm2 start /home/slock/public_html/slock/Backend/backend/Commander/mqttAlarmBar.py --interpreter /home/slock/enviroments/env/bin/python3 --name AlarmBar

#BASE_URL_OPERATIONS = 'http://127.0.0.1:8000/api/slock'
BASE_URL_OPERATIONS = 'https://slock.com.br/api/slock'

topic_rfid_send = 'alarm/bar/maycon/uc/send/dev'
topic_rfid_receiver = 'alarm/bar/maycon/uc/receiver'

time_interval_registers = 5 # Minute

call_enable = False

# Só liga com o número 3
def call(phone_number_from, phone_number_to):
    
    try:    
        
        print(f'\nIniciando ligacao from: {phone_number_from}\n Para: {phone_number_to}')
        
        client = Client('AC110c01d49b3fdee15ddbb81846e5c430', '00cd33c6d912deb5c194c7b082b11088')                
                
        call = client.calls.create(            
            twiml=f'<Response><Play>https://slock.com.br/static/Twilio/Audio/AlarmBar/disparo_teste.mp3</Play></Response>',    
            to=f"{phone_number_to}",
            from_=f"{phone_number_from}"
        )        
        
    except Exception as e:
        print(e)

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
        # print(f'Payload in str: \n{payload_str}\n\n')  
        # print(f'Dados Bruto da request: \n{data}\n\n')          
        # print(f'Function: {data["fn"]}\n')  
        # print(f'Topico: {msg.topic}\n')  

        if msg.topic == topic_rfid_send:          
            if 'imu_alarm_on' in data["fn"]:                
                
                alarm_bar_id = extrair_id(data['id'])
                con = psycopg2.connect(host='slock.com.br', dbname='slock', user='smainex', password='smainex@22072025')

                # Pegar a última chamada
                querySelect = f"""
                    SELECT 
                        q.id,
                        q.created_at,
                        CASE 
                            WHEN q.created_at < NOW() - INTERVAL '{time_interval_registers} minutes' THEN 'SIM'
                            ELSE 'NAO'
                        END AS passou_{time_interval_registers}_minutos
                    FROM 
                        alarm_bar_disparo q
                    ORDER BY 
                        q.created_at DESC
                    LIMIT 1;
                """                
                
                with con.cursor() as cur:
                    
                    # Executar a consulta
                    cur.execute(querySelect)

                    # Recuperar o resultado
                    resultado = cur.fetchone()

                    # Exibir o resultado
                    if resultado:
                        id, created_at, passou_1_minutos = resultado
                        print(f"ID: {id}, \t Criado em: {created_at}, \t Ja passou mais de {time_interval_registers} minutos? {passou_1_minutos}")
                    else:
                        print("Nenhum registro encontrado.")                                                    
                        passou_1_minutos = 'SIM'
                        
                    # Disparo
                    sql1 = f"""
                        INSERT INTO alarm_bar_disparo (alarm_bar, pitch, roll, yaw, created_at) VALUES (                        
                            {alarm_bar_id}, {data['pitch']}, {data['roll']}, {data['yaw']}, NOW()
                        );
                    """
                    cur.execute(sql1)
                    print('+1 Disparo anotado em bom sucesso')
                
                    if passou_1_minutos == 'SIM':                                                
                        
                        print(f'Entrou no bloco da call\n')
                        print(f'Call enable: {call_enable}\n')
                        
                        # Add na Queue de ligação
                        number_from = f'+17066618382'
                        number_to = f'+5546991310160'
                        sql2 = f"""
                            insert into queue (
                                number_from, number_to, created_at, pendent
                            ) values(
                                '{number_from}', '{number_to}', NOW(), false
                            )
                        """
                        cur.execute(sql2)
                        
                        if call_enable:
                            call(number_from, number_to)
                            print('\t+1 Call')
                        
                    con.commit()                        
                    
                con.close()                
                
            else:
                print('Nao tem funcao para esse comando')  
        else:
            print('Nao tem tratamento para este topico')                        
            
              
    except Exception as e:
        print('erro: ' + str(e))



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

def extrair_id(texto):
    match = re.search(r'#id-mqtt-(\d+)', texto)
    if match:
        return int(match.group(1))
    return None


qtd_errors = 0

while True:
    print("WELCOME TO SERVER - OPERATIONS")
    data = datetime.datetime.now()
    # Connect
    mqttc.username_pw_set('AUTEN_SLOCKER', 'AUTEN_slocker@20052022')
    mqttc.connect('slock.com.br', 1883)

    # Start subscribe, with QoS level 0
    mqttc.subscribe(topic_rfid_send, 0)

    # Publish a message
    # mqttc.publish(topic, "my message")

    # Continue the network loop, exit when an error occurs
    rc = 0
    while rc == 0:
        rc = mqttc.loop()

    qtd_errors = qtd_errors + 1
    print("Data e Hora: " + str(data) + "rc: " + str(rc) + "Qtde Errors: " + str(qtd_errors))



