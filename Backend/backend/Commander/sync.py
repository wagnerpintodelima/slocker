from calendar import month
import paho.mqtt.client as mqtt
import os
import psycopg2
import datetime
import requests
import json
from SGBD import BD

# A ideia aqui é pegar o banco todo e sincronizar mas vai ficar para frente
# porque o banco vai ficar grande aí é foda lá no futuro

bd = BD()

def main():    
    
    condominos = bd.select('select * from condomino;')
    
    for c in condominos:
        print(c['nome'])



if __name__ == "__main__":        
    try:
        main()
    finally:
        print('Finalizado')





