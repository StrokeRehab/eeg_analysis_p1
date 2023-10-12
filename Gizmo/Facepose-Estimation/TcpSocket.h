#ifndef TCPSOCKET_H
#define TCPSOCKET_H

#include <arpa/inet.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/types.h> // for sockets
#include <unistd.h>
#include <functional>

using namespace std;

class TcpSocket
{
public:
   TcpSocket();
   TcpSocket(const char *port);
   TcpSocket(const char *port, const char *address);

   int send(char *msg, int msgSize);

   // /**
   //  * start multithreaded server. This requires a struct that defines the data to be passed to each thread, and a function that defines what the thread will do
   //  */
   // int startServer(void *threadData, function<void *(void *)> threadFunction);

   struct
   {
   } ThreadData;

private:
   const int MAX_REQUESTS = 20;
   const char *port;
   const char *address;
   int sd;

   int createTcpSocket(const char *port, const char *server);
   int createNewSocket(addrinfo *servInfo);
   int serverListenThread(void *threadData, function<void *(void *)> threadFunction);
};

#endif
