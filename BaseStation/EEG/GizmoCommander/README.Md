# Running GizmoCommander
GizmoCommander is completely containerized, so if you know how to use docker, then you should have no problem starting it and troubleshooting.
Important: If you need to change ports/IPs of different components that communicate with GizmoCommander, you can do so by editing the ENV variables
in the Dockerfile and rebuilding the image (don't forget to delete the old container in the registry!). More info about this below.

## How you usually start it (if everything is working)
If GizmoCommander has already been built and run on the machine, you should just be able to start the image with: `sudo docker start GizmoCommander`

## Viewing Output/logs
You can view the GizmoCommander program output with: `sudo docker logs GizmoCommander`
If you want to see real-time logs type: `sudo docker logs -f GizmoCommander`

## How to stop it
To stop GizmoCommander: `sudo docker stop GizmoCommander`

## Troubleshooting

If you attempted to run `sudo docker start GizmoCommander`
And you received this error: 
> `Error response from daemon: No such container: GizmoCommander`
> `Error: failed to start containers: GizmoCommander`

This means that you need to run the container to create a new container instance in the registry that you can start/stop
type: `./build.sh`
Then type: `./run.sh`

The container will now be running. To turn it off, you may have to log in from a different terminal and type: `sudo docker stop GizmoCommander`

You can now start/stop the container whenever you want. If you ever change the Dockerfile or the python files, you will need to rebuild the container and then run it.
When rebuilding and running you may get this error: 

> `docker: Error response from daemon: Conflict. The container name "/GizmoCommander" is already in use by container "97965db397d10cc1677dedb8c09071d4c15e57a05367b7b4ba99c6648daeec51". You have to remove (or rename) that container to be able to reuse that name.
> See 'docker run --help'.`
  
In this case, you need to delete the old container from the Docker registry before running the updated version. You can see the full registry with: `sudo docker ps -a`
Type: `sudo docker rm GizmoCommander`
This will remove GizmoCommander container from the registry, and you can now `./run.sh` to create the updated container

As for connecting GizmoCommander to the other programs in the system. You can change the IPs and port numbers in the Dockerfile. Then rebuild,run
