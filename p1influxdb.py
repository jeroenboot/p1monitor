#!/usr/bin/python
import time
import sys
import serial
import datetime
from influxdb import InfluxDBClient

versie = "1.1"





#Configure InfluxDB connection variables
host = "127.0.0.1"  # My Ubuntu NUC
port = 8086  # default port
user = "xxxx"  # the user/password created for the pi, with write access
password = "xxxx"
dbname = "xxxx" # the database we created earlier
interval = 10 # Sample period in seconds

# Create the InfluxDB client object
client = InfluxDBClient(host, port, user, password, dbname)

measurement = "p1-jeroen" # soort van "tabel"

##############################################################################
#Main program
##############################################################################
print ("DSMR P1 uitlezen",  versie)
print ("Control-C om te stoppen")
print ("Pas eventueel de waarde ser.port aan in het python script")

#Set COM port config
ser = serial.Serial()
ser.baudrate = 115200
ser.bytesize=serial.EIGHTBITS
ser.parity=serial.PARITY_NONE
ser.stopbits=serial.STOPBITS_ONE
ser.xonxoff=0
ser.rtscts=0
ser.timeout=20
ser.port="/dev/ttyAMA0"

#Open COM port
try:
    ser.open()
except:
    sys.exit ("Fout bij het openen van %s. Aaaaarch."  % ser.name)



#Initialize
# stack is mijn list met de 26 regeltjes ingelezen uit de P1 poort
iso = time.ctime()
regels = 26
p1_teller=0
stack=[]

while p1_teller < regels:
    p1_line=''

    try:
        p1_raw = ser.readline()
    except:
        sys.exit ("Seriele poort %s kan niet gelezen worden. Programma afgebroken." % ser.name )
    p1_str=str(p1_raw)
    p1_line=p1_str.strip()
    stack.append(p1_line)
    # als je alles wil zien moet je de volgende line uncommenten
    #print (p1_line)

    p1_teller = p1_teller +1 #lekker blijven uitlezen tot max (regels)


#Extract informatui uit de regels (stack)
stack_teller=0

while stack_teller < regels:

    if stack[stack_teller][0:9] == "1-0:1.8.1":
        dalverbruik = float(stack[stack_teller][10:20])
        print "dalverbruik     ", dalverbruik, " kWh"
    elif stack[stack_teller][0:9] == "1-0:1.8.2":
        piekverbruik = float(stack[stack_teller][10:20])
        print "piek verbruik   ", piekverbruik, "kWh"
    # Daltarief, teruggeleverd vermogen 1-0:2.8.1
    elif stack[stack_teller][0:9] == "1-0:2.8.1":
        dalterug = float(stack[stack_teller][10:20])
        print "dalterug   ", dalterug, "kWh"
    # Piek tarief, teruggeleverd vermogen 1-0:2.8.2
    elif stack[stack_teller][0:9] == "1-0:2.8.2":
        piekterug = float(stack[stack_teller][10:20])
        print "piekterug  ", piekterug, "kWh"
    # Huidige stroomafname: 1-0:1.7.0
    elif stack[stack_teller][0:9] == "1-0:1.7.0":
        vermogenaf = int(float(stack[stack_teller][10:16])*1000)
        print "afgenomen vermogen      ", vermogenaf, " W"
    # Huidig teruggeleverd vermogen: 1-0:1.7.0
    elif stack[stack_teller][0:9] == "1-0:2.7.0":
        vermogenterug = int(float(stack[stack_teller][10:16])*1000)
        print "teruggeleverd vermogen  ", vermogenterug, " W"
    # Huidige netspanning: 1-0:32.7.0
    elif stack[stack_teller][0:10] == "1-0:32.7.0":
        spanning = float(stack[stack_teller][11:14])
        print "Huidige netspanning.    ", spanning, " Volt"
    # Gasmeter: 0-1:24.2.1
    elif stack[stack_teller][0:10] == "0-1:24.2.1":
        gas = float(stack[stack_teller][26:35])
        print "Gas                     ", gas, " dm3"
    else:
        pass
    stack_teller = stack_teller +1




# Create the JSON data structure voor InfluxDB

totaalverbruik = dalverbruik + piekverbruik # dal + piek (tarief1 +tarief2)
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

print data


# Send the JSON data to InfluxDB
client.write_points(data)


#Close port and show status
try:
    ser.close()
except:
    sys.exit ("Oops %s. Programma afgebroken." % ser.name )
