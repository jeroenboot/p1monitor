# built
Create a (Docker) image, see attached Dockerfile  
```
docker build -t jeroenboot/p1serial .
```

# run
Run on the same host (network = host)  

```
docker run \
 --restart unless-stopped \
 --detach \
 --net=host \
 --name=p1serial \
 --device /dev/ttyAMA0:/dev/ttyAMA0 \
 jeroenboot/p1serial
```
