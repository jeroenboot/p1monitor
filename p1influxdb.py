#!/usr/bin/python3
import time
import sys
import serial
import datetime
import json
from influxdb import InfluxDBClient
import paho.mqtt.client as mqtt


#Configure InfluxDB connection variables
host = "192.168.5.30"
port = 8086  # default port
user = "admin"  # the user/password created for the pi, with write access
password = "admin"
dbname = "p1data" # the database we created earlier
interval = 10 # Sample period in seconds

# Create the InfluxDB client object
client = InfluxDBClient(host, port, user, password, dbname)
measurement = "p1-jeroen" # soort van "tabel"



#Configure MQTT
mqtt_broker_address="192.168.5.30"
mqtt_client = mqtt.Client("p1monitor")
mqtt_topic = "p1monitor/out"


#Set COM port config
ser = serial.Serial()
ser.baudrate = 115200
ser.bytesize=serial.EIGHTBITS
ser.parity=serial.PARITY_NONE
ser.stopbits=serial.STOPBITS_ONE
ser.xonxoff=0
ser.rtscts=0
ser.timeout=20
ser.port="/dev/ttyUSB0"


# stack is mijn list met de 26 regeltjes ingelezen uit de P1 poort
regels = 26

##############################################################################
#Main program
##############################################################################

# Init MQTT
try:
    mqtt_client.connect(mqtt_broker_address)

except Exception as ex:
    print("Cannot connect to MQTT: {0}".format(str(ex)))
    exit(1)



#Open COM port
try:
    ser.open()
except:
    sys.exit ("Fout bij het openen van %s. Aaaaarch."  % ser.name)

p1_teller=0
stack_teller=0
p1_line=''
stack=[]

while p1_teller < regels: #P1 blijven uitlezen en lijnen in een stack plaatsen
    try:
        p1_raw = ser.readline()
    except:
        sys.exit ("Seriele poort %s kan niet gelezen worden. Programma afgebroken." % ser.name )
    p1_str=str(p1_raw.decode('UTF-8'))
    p1_line=p1_str.strip()
    stack.append(p1_line)
    p1_teller = p1_teller +1 #lekker blijven uitlezen tot max (regels)
    print(p1_teller, p1_line)


while stack_teller < regels: #stack ontleden
    if stack[stack_teller][0:9] == "1-0:1.8.1":
        dalverbruik = float(stack[stack_teller][10:20])
    elif stack[stack_teller][0:9] == "1-0:1.8.2":
        piekverbruik = float(stack[stack_teller][10:20])
    # Daltarief, teruggeleverd vermogen 1-0:2.8.1
    elif stack[stack_teller][0:9] == "1-0:2.8.1":
        dalterug = float(stack[stack_teller][10:20])
    # Piek tarief, teruggeleverd vermogen 1-0:2.8.2
    elif stack[stack_teller][0:9] == "1-0:2.8.2":
        piekterug = float(stack[stack_teller][10:20])
    # Huidige stroomafname: 1-0:1.7.0
    elif stack[stack_teller][0:9] == "1-0:1.7.0":
        vermogenaf = int(float(stack[stack_teller][10:16])*1000)
    # Huidig teruggeleverd vermogen: 1-0:1.7.0
    elif stack[stack_teller][0:9] == "1-0:2.7.0":
        vermogenterug = int(float(stack[stack_teller][10:16])*1000)
    # Huidige netspanning: 1-0:32.7.0
    elif stack[stack_teller][0:10] == "1-0:32.7.0":
        spanning = float(stack[stack_teller][11:14])
    # Gasmeter: 0-1:24.2.1
    elif stack[stack_teller][0:10] == "0-1:24.2.1":
        gas = float(stack[stack_teller][26:34])
    else:
        pass
    stack_teller = stack_teller +1

# Create the JSON data structure voor InfluxDB
totaalverbruik = piekverbruik + dalverbruik
data = [
    {
        "measurement": measurement,
        "fields": {
            "dalverbruik": dalverbruik,
            "piekverbruik": piekverbruik,
            "totaalverbruik": totaalverbruik,
            "dalterug": dalterug,
            "piekterug": piekterug,
            "vermogenaf": vermogenaf,
            "vermogenterug":vermogenterug,
            "spanning":spanning,
            "gas":gas
        }
    }
]

#debug
print(data)

# Send the JSON data to InfluxDB
client.write_points(data)
print('data sent to InfluxDB')

# Send data to MQTT broker
mqtt_client.publish(mqtt_topic, json.dumps(data))
mqtt_client.disconnect()
print('data sent to broker')