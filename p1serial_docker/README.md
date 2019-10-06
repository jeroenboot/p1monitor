# built
Create a (Docker) image, see attached Dockerfile  
```
docker build -t jeroenboot/p1serial .
```

# run
Run on the same host (network = host) as influxDB    
```
docker run \
 --restart unless-stopped \
 --detach \
 --net=host \
 --name=p1serial \
 --device /dev/ttyAMA0:/dev/ttyAMA0 \
 -e PYTHONUNBUFFERED=0 \
 jeroenboot/p1serial
```

# check
JSON string is being logged in container  
```
docker logs p1serial
```
