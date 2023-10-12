#!/bin/bash

export PYTHONPATH="/home/pierremourad/Desktop/FE/SRP/Facepose-Estimation:/usr/lib/python36.zip:/usr/lib/python3.6:/usr/lib/python3.6/lib-dynload:/home/pierremourad/.local/lib/python3.6/site-packages:/usr/local/lib/python3.6/dist-packages:/usr/lib/python3/dist-packages:/usr/lib/python3.6/dist-packages"

trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

./ServoServer.py &
./FaceposeEstimation.exe &

wait

