FROM python:3.11.1

WORKDIR /app

# Specify locales, or we encounter Python Syntax Erro for Non-UTF-8 character
# https://stackoverflow.com/questions/27931668/encoding-problems-when-running-an-app-in-docker-python-java-ruby-with-u
RUN apt update && apt -y install locales
# Set the locale
RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  

COPY . .

# RUN python3.11 get-pip.py

RUN pip install -r requirements.txt

# port of tcp client sending EEG classification data
ENV EEG_PORT=26783
#port of tcp client sending facepose estimation results (server is running on gizmo)
ENV GIZMO_PORT=26784
# Address of gizmo
ENV GIZMO_ADDRESS='10.19.116.92'
# Port on gizmo that is recieving directions
ENV GIZMO_DIRECTOR_PORT=40000

EXPOSE ${EEG_PORT}
EXPOSE ${GIZMO_PORT}





CMD python3 -u gizmoCommander.py -ga ${GIZMO_ADDRESS} -gdp ${GIZMO_DIRECTOR_PORT} -ep ${EEG_PORT} -gp ${GIZMO_PORT}

# `python#.#-dev`: includes development headers for building C extensions
# - `python#.#-venv`: provides the standard library `venv` module
# - `python#.#-distutils`: provides the standard library `distutils` module
# - `python#.#-lib2to3`: provides the `2to3-#.#` utility as well as the standard library `lib2to3` module
# - `python#.#-gdbm`: provides the standard library `dbm.gnu` module
# - `python#.#-tk`: provides the standard library `tkinter` module





