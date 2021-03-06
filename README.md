<img width="1792" alt="Schermafbeelding 2019-10-04 om 13 53 16" src="https://user-images.githubusercontent.com/23233001/66209640-13ad3480-e6b8-11e9-91cb-a23270b1c215.png">


# Inleiding

Deze howto beschrijft hoe je via een raspberrypi een (slimme) elektra en gasmeter kan uitlezen over een P1 poort en deze gegevens weergeven in mooie grafieken. Om het interessant te maken worden alle processen in (micro)services geplaatst, welke op het Docker runtime komen te draaien.

Het publiek is voor beginners, met een interesse in Dockers, Python, Grafana, en InfluxDB.
Enige kennis van Linux (en solderen) is een pre.

In 15 "simpele" stappen heb je een raspberry waarin alle P1 informatie wordt opgeslagen en weergegeven :-)



## Wat is een P1 poort

De P1 poort is een seriele poort op je digitale elektra meter waarin je een RJ-11 (Registered Jack) stekkertje kan steken (bekend van de telefoonaansluitingen) om zo de meterstanden en het verbruik uit te lezen. Het serieel signaal is echter niet direct bruikbaar. Eerst zal het signaal geïnverteerd moeten worden.




## Stappenplan

**1.	Download raspbian (Debian 10/Buster voor raspberry)**  
https://downloads.raspberrypi.org/raspbian_lite_latest  
**2.	Schrijf image naar sdcard**  
Ik gebruik hier BalenaEtcher voor; https://www.balena.io/etcher/  
**3.	Plaats een leeg bestand, genaamd ssh, in de boot partitie van het geschreven image**  
**4.	First boot raspbian en test seriele verbinding**  
SSH inloggen en testen (username pi, passwords raspberry)  
Installeer minicom   
```
sudo apt-get install -y minicom cu
```
**5.	Activeer serial connections (disable serial login, enable hardware)** .
![serieel](https://user-images.githubusercontent.com/23233001/66252523-1d3ca800-e75d-11e9-8f6d-4b8d118a86aa.png)

**6.	Soldeer inverter en sluit aan de Raspberry (zie onderstaand schema)** .
```
2*  10K weerstand
1*  1K weerstand
1*  transistor (bc547)
6*  headers en kabels
1*  RJ11 kabeltje
```
**Voor voor ESMRv5 (Iskra/AM550) heb ik een 4.7K tussen P2 (RTS) en P5 (Data) nodig**  
*Via AliExpress of Conrad kan je simpel alle onderdelen bestellen*
![schema](https://user-images.githubusercontent.com/23233001/66252535-452c0b80-e75d-11e9-8892-b60d483f41c2.png)

**7.  Test werking**  
*Op http://domoticx.com/p1-poort-slimme-meter-hardware/ staan de instellingen voor alle meters*

```
sudo cu -l /dev/ttyAMA0 -s 115200 --parity=none
```
*Daar komen de berichten (telegrams):*
<br>
```
/ISK5\2M550E-1012

1-3:0.2.8(50)
0-0:1.0.0(190927140105S)
0-0:96.1.1(4530303433303037333930363836xxxxx)
1-0:1.8.1(000278.797*kWh)
1-0:1.8.2(000289.674*kWh)
1-0:2.8.1(000000.000*kWh)
1-0:2.8.2(000000.000*kWh)
0-0:96.14.0(0002)
1-0:1.7.0(00.384*kW)
1-0:2.7.0(00.000*kW)
0-0:96.7.21(00007)
0-0:96.7.9(00003)
1-0:99.97.0(1)(0-0:96.7.19)(190416205856S)(0000000205*s)
1-0:32.32.0(00005)
1-0:32.36.0(00001)
0-0:96.13.0()
1-0:32.7.0(223.2*V)
1-0:31.7.0(001*A)
1-0:21.7.0(00.385*kW)
1-0:22.7.0(00.000*kW)
0-1:24.1.0(003)
0-1:96.1.0(4730303339303031373638323537343137)
0-1:24.2.1(190927140007S)(00910.135*m3)
!582D
```


**8. Configureer de raspberry, want de seriele verbinding werkt naar behoren :-)**  
Software and PI update  
```
$sudo apt-get update
$sudo apt-get dist-upgrade -y
$sudo rpi-update
```

Filesystem (TMPFS) om de SDCARD te ontlasten  
```
$sudo vi /etc/fstab

tmpfs    /tmp               tmpfs   defaults,noatime,nosuid,size=30m                    0 0
tmpfs    /var/tmp           tmpfs   defaults,noatime,nosuid,size=30m                    0 0
tmpfs    /var/log           tmpfs   defaults,noatime,nosuid,mode=0755,size=30m          0 0
tmpfs    /var/spool/mqueue  tmpfs   defaults,noatime,nosuid,mode=0700,gid=1001,size=30m 0 0
```

Aanpassen Raspberry configuratie  
```
$sudo raspi-config
-	Update utility  
-	Timezone  
-	Hostname  
-	Expand memory/disk  
-	Password (pi user)
```

Disable swap om de SDCARD te ontlasten  
```
$sudo swapoff --all
$sudo atp-get remove dphys-swapfile
```

Unattended upgrades (en update patterns)  
```
$sudo apt-get install unattended-upgrades
$sudo nano /etc/apt/apt.conf.d/50unattended-upgrades


Unattended-Upgrade::Origins-Pattern {
        // Codename based matching:
        // This will follow the migration of a release through different
        // archives (e.g. from testing to stable and later oldstable).
        // Software will be the latest available for the named release,
        // but the Debian release itself will not be automatically upgraded.
        "origin=Debian,codename=${distro_codename}-updates";
        "origin=Debian,codename=${distro_codename}-proposed-updates";
        "origin=Debian,codename=${distro_codename},label=Debian";
        "origin=Debian,codename=${distro_codename},label=Debian-Security";

        ****"origin=Raspbian,codename=${distro_codename},label=Raspbian";
        "origin=Raspberry Pi Foundation,codename=${distro_codename},label=Raspberry Pi Foundation";****


        // Archive or Suite based matching:
        // Note that this will silently match a different release after
        // migration to the specified archive (e.g. testing becomes the
        // new stable).
//      "o=Debian,a=stable";
//      "o=Debian,a=stable-updates";
//      "o=Debian,a=proposed-updates";
//      "o=Debian Backports,a=${distro_codename}-backports,l=Debian Backports";
};
```

f.  Aanpassen auto-upgrades  
*Vervang bestaande configuratie voor:*
```
$sudo nano /etc/apt/apt.conf.d/20auto-upgrades
```

```
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Verbose "1";
APT::Periodic::AutocleanInterval "7";
```

To enable unattended updates type:  
```
$sudo dpkg-reconfigure --priority=low unattended-upgrades
```

**9.  Docker installatie op PI**  
Installatie Docker-runtime en toevoegen van de pi user als docker-gebruiker.
```
$curl -fsSL https://get.docker.com -o get-docker.sh
$sudo sh get-docker.sh
$sudo usermod -aG docker pi
```

Persistent storage/volume(s) voor database en grafieken  
*Waarschijnlijk moet je opnieuw inloggen om de toegevoegde groep (docker) te kunnen gebruiken.*
```
$docker volume create grafana-volume
$docker volume create influxdb-volume
```



**10. Grafana**  
***The open observability platform, Grafana is the open source analytics & monitoring solution for every database***

*Super simpel met Docker*  
*Eventueel kan je hier ook een Docker compose voor gebruiken om meerdere containters tegelijk op te starten*
```
docker run \
 --restart unless-stopped \
 --detach \
 --net=host \
 --name=grafana \
 --volume=grafana-volume:/var/lib/grafana \
 grafana/grafana
```  
*inloggen kan nu naar http://$raspberryip:3000 met: admin:admin*

![grafana](https://user-images.githubusercontent.com/23233001/66252530-304f7800-e75d-11e9-8d16-fde53f2429fa.png)
*Eventueel de logs bekijken tijdens het opstarten*
```
docker logs grafana
```

**11. InfluxDB**  
***InfluxDB is an open-source time series database (TSDB) developed by InfluxData. It is written in Go and optimized for fast, high-availability storage and retrieval of time series data in fields such as operations monitoring, application metrics, Internet of Things sensor data, and real-time analytics.***  

*Super simpel met Docker*
```
docker run -p 8086:8086 \
      --restart unless-stopped \
      --detach \
      --name=influxdb \
      -e INFLUXDB_DB=p1data \
      -e INFLUXDB_ADMIN_USER=admin \
      -e INFLUXDB_ADMIN_PASSWORD=admin \
      -e INFLUXDB_USER=user \
      -e INFLUXDB_USER_PASSWORD=user \
      -v influxdb-volume:/var/lib/influxdb \
      influxdb:latest
```
*Eventueel de logs bekijken tijdens het opstarten*  
```
docker logs influxdb
```

Aanmaken van de database  
```
docker exec -it influxdb /usr/bin/influx
create database "p1data"
```


**12. Python container**  
*Python wordt gebruikt om daadwerkelijk de data van de P1 naar de influxdb te sturen.  
Deze informatie draait in een (micro)service, zie: https://github.com/jeroenboot/p1monitor/blob/master/p1serial_docker/README.md*

Een alternatief is het python script (p1influxdb.py) uitvoeren via de crontab:
```
* * * * * /home/pi/p1/p1influxdb.py >/dev/null 2&1
* * * * * ( sleep 10 ; /home/pi/p1/p1influxdb.py >/dev/null 2>&1 )
* * * * * ( sleep 20 ; /home/pi/p1/p1influxdb.py >/dev/null 2>&1 )
* * * * * ( sleep 30 ; /home/pi/p1/p1influxdb.py >/dev/null 2>&1 )
* * * * * ( sleep 40 ; /home/pi/p1/p1influxdb.py >/dev/null 2>&1 )
* * * * * ( sleep 50 ; /home/pi/p1/p1influxdb.py >/dev/null 2>&1 )
```

**13. influxDB koppelen aan Grafana**  
![influxdb](https://user-images.githubusercontent.com/23233001/66252526-2cbbf100-e75d-11e9-95ce-bc2cb55117ac.png)

**14. Dashboard inladen**  
https://github.com/jeroenboot/p1monitor/blob/master/dashboard.json

Via: **Dashboards -> Manage -> Import -> json file**  

**15. Alle informatie is nu gekoppeld :-)**  
*Eventuele aanpassingen in scripts en databases aanpassen in de grafieken*
