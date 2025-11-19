from calendar import month
import paho.mqtt.client as mqtt
import os
import psycopg2
import datetime
import requests
import json



# pm2 start --interpreter ..\..\venv\Scripts\activate .\mqtt.py

#BASE_URL_OPERATIONS = 'http://127.0.0.1:8000/api/slock'
BASE_URL_OPERATIONS = 'https://slock.com.br/api/slock'
topic_slocker = 'auten/slocker/api/send'
topic_slocker_receiver = 'auten/slocker/api/receiver'


# Define event callbacks
def on_connect(client, userdata, flags, rc):
    print("onConnect: " + str(rc))


def on_message(client, obj, msg):
    try:
        # Obtém a data e hora atuais
        now = datetime.datetime.now()
        formatted_date_time = now.strftime("%d/%m/%Y %H:%M:%S")

        # Converte o payload para uma string
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
        print(f'Dados Bruto da request: \n{data}')

        con = psycopg2.connect(host='slock.com.br', dbname='slock',
                               user='smainex', password='smainex@22072025')
        cur = con.cursor()
        # sql = "INSERT INTO mqtt VALUES(default, '{}', now())".format(str(msg_))
        # cur.execute(sql)
        # con.commit()

        if msg.topic == topic_slocker:

            cSQL = """
                select a.id
                from automation a 
                where a.mac ilike '{}'
                limit 1
            """.format(data['mac'])

            # Executa a consulta
            cur.execute(cSQL)

            # Obtém o resultado da consulta
            automation_id = cur.fetchone()[0]

            if not automation_id:
                print("Automation id not found")
            else:
                if 'bateria_start' in data:
                    print("START BATERIA")
                    print("Topic: " + msg.topic)
                    print("DataHora  : " + formatted_date_time)
                    print("MAc  : " + data['mac'])
                    print("Tensao bateria  : " + data['bateria_start'])
                    print("____________________________________")

                    cSQL = """
                        INSERT INTO battery 
                        (automation_id, "key", "value", created_at)
                        VALUES({}, 'bateria_start', '{}', CURRENT_TIMESTAMP)
                    """.format(automation_id, data['bateria_start'])
                    cur.execute(cSQL)
                    con.commit()

                elif 'bateria_end' in data:
                    print("____________________________________")
                    print("END BATERIA")
                    print("Topic: " + msg.topic)
                    print("DataHora  : " + formatted_date_time)
                    print("MAc  : " + data['mac'])
                    print("Tensao bateria  : " + data['bateria_end'])
                    print("____________________________________")

                    cSQL = """
                        INSERT INTO battery 
                        (automation_id, "key", "value", created_at)
                        VALUES({}, 'bateria_end', '{}', CURRENT_TIMESTAMP)
                    """.format(automation_id, data['bateria_end'])
                    cur.execute(cSQL)
                    con.commit()

                elif 'bateria' in data:
                    print("____________________________________")
                    print("BATERIA by hour")
                    print("Topic: " + msg.topic)
                    print("DataHora  : " + formatted_date_time)
                    print("MAc  : " + data['mac'])
                    print("Tensao bateria  : " + data['bateria'])
                    print("____________________________________")

                    cSQL = """
                        INSERT INTO battery 
                        (automation_id, "key", "value", created_at)
                        VALUES({}, 'bateria', '{}', CURRENT_TIMESTAMP)
                    """.format(automation_id, data['bateria'])
                    cur.execute(cSQL)
                    con.commit()

                elif 'fn_update_datetime' in data:
                    print("____________________________________")
                    print("STM32F407vet6 -> ESP32 -> Solicita atualizacao de data e hora")
                    print("Topic: " + msg.topic)
                    print("DataHora  : " + formatted_date_time)
                    print("Mac  : " + data['mac'])
                    print("____________________________________")

                    day = str(now.strftime("%d"))
                    month = str(now.strftime("%m"))
                    year = str(now.strftime("%y"))
                    hour = str(now.strftime("%H"))
                    minutes = str(now.strftime("%M"))
                    seconds = str(now.strftime("%S"))

                    packageMqtt = {
                        'mac': data['mac'],
                        'function': 'sync_datetime',
                        'day': day,
                        'month': month,
                        'year': year,
                        'hour': hour,
                        'minute': minutes,
                        'seconds': seconds
                    }

                    mqttc.publish(topic_slocker_receiver, json.dumps(packageMqtt))

                elif 'fn_delivered' in data:
                    print("___________NEW DELIVERED_____________")
                    print("Mac: {}".format(data['mac']))
                    print("DataHora  : " + formatted_date_time)
                    print("Ap  : " + data['ap'])
                    print("Slot  : " + data['slot'])
                    url = "{}/checkout/delivered".format(BASE_URL_OPERATIONS)
                    print("Enviando para django... na url: {}".format(url))
                    response = requests.post(url, json=data)
                    print("Enviado: {}".format(json.dumps(response.json(), indent=4)))
                    print("____________________________________")

                elif 'fn_load_pswd_slot' == data['function']:
                    print("________Enviar Listas de Senhas dos slots ocupados_____")
                    print("Mac: {}".format(data['mac']))
                    print("DataHora  : " + formatted_date_time)
                    url = "{}/refresh/pswd/slots".format(BASE_URL_OPERATIONS)
                    print("Enviando para django... na url: {}".format(url))
                    response = requests.post(url, json=data)
                    print("Enviado: {}".format(response.text))
                    print("____________________________________")

                elif 'show_json_checkouts' == data['function']:
                    print("________Recebendo JSON de Checkouts a partir do SD card_____")
                    print("Mac: {}".format(data['mac']))
                    print("DataHora  : " + formatted_date_time)
                    url = "{}/checkout/receive/json/from/sd".format(BASE_URL_OPERATIONS)
                    print("Enviando para django... na url: {}".format(url))
                    response = requests.post(url, json=data)
                    print("Enviado: {}".format(json.dumps(response.json(), indent=4)))
                    print("____________________________________")
                else:
                    print('Essa request nao foi executada por nenhum processo da API.')

        # Fecha a conexão com o banco de dados
        cur.close()
        con.close()

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



qtd_errors = 0

while True:
    print("WELCOME TO SERVER - OPERATIONS")
    data = datetime.datetime.now()
    # Connect
    mqttc.username_pw_set('AUTEN_SLOCKER', 'AUTEN_slocker@20052022')
    mqttc.connect('slock.com.br', 1883)

    # Start subscribe, with QoS level 0
    mqttc.subscribe(topic_slocker, 0)

    # Publish a message
    # mqttc.publish(topic, "my message")

    # Continue the network loop, exit when an error occurs
    rc = 0
    while rc == 0:
        rc = mqttc.loop()

    qtd_errors = qtd_errors + 1
    print("Data e Hora: " + str(data) + "rc: " + str(rc) + "Qtde Errors: " + str(qtd_errors))



