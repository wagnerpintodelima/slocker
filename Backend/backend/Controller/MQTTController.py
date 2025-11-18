import paho.mqtt.client as mqtt
from unidecode import unidecode

from slock.settings import MQTT_PUBLISH_TOPIC, MQTT_SUBSCRIBER_TOPIC

import random
import string



def mqttSendDataToDevice(mensagem, topic=MQTT_PUBLISH_TOPIC):

    print(f'MQTT\tMensagem: {mensagem}\tTopico: {topic}')

    mqttc = mqtt.Client()
    # Assign event callbacks
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_publish = on_publish
    mqttc.on_subscribe = on_subscribe

    # Connect
    mqttc.username_pw_set('AUTEN_SLOCKER', 'AUTEN_slocker@20052022')
    mqttc.connect('slock.com.br', 1883)

    mqttc.publish(topic, mensagem)

    return True


# Define event callbacks
def on_connect(client, userdata, flags, rc):
    print("rc: " + str(rc))

def on_message(client, obj, msg):
    print(msg_ = msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def on_publish(client, obj, mid):
    print("mid: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(client, obj, level, string):
    print(string)


def remover_acentos(texto):
    texto_sem_acentos = unidecode(texto)
    return texto_sem_acentos



def generate_password(length=5):
    """
    Gera uma senha aleatória com o comprimento especificado.
    A senha é composta por dígitos numéricos de 0 a 9.

    Args:
    - length: O comprimento da senha desejada. Padrão é 8 caracteres.

    Retorna:
    - Uma string representando a senha gerada.
    """
    # Define os caracteres possíveis: dígitos de 0 a 9
    chars = string.digits

    # Gera a senha selecionando caracteres aleatórios da string de caracteres possíveis
    password = ''.join(random.choice(chars) for _ in range(length))

    return password