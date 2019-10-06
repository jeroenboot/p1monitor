FROM python:3

ADD p1serial.py /
RUN pip install pyserial influxdb
CMD [ "python","-u","./p1serial.py" ]
