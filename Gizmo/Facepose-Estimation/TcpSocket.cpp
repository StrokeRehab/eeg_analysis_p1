#include "TcpSocket.h"
#include <stdexcept>
#include <iostream>
#include <cstring>

using namespace std;

TcpSocket::TcpSocket()
{
   // temp object constructure
   sd = -1;
}
// create client
TcpSocket::TcpSocket(const char *port, const char *address) : port(port), address(address)
{
   sd = createTcpSocket(port, address);
   if (sd < 0)
   {
      throw runtime_error("Could not connect to TCP server at " + *address + ':' + *port);
   }
}

TcpSocket::TcpSocket(const char *port) : port(port), address(nullptr)
{
   // create server
   sd = createTcpSocket(port, NULL);
   if (sd < 0)
   {
      throw runtime_error("Could not start TCP server at port " + *port);
   }
}

int TcpSocket::createTcpSocket(const char *port, const char *server)
{
   // create server info structure
   struct addrinfo hints, *servInfo; // loaded with getaddrinfo()
   memset(&hints, 0, sizeof(hints)); // initialize memory in struct hints
   hints.ai_family = AF_UNSPEC;      // use IPv4 or IPv6
   hints.ai_socktype = SOCK_STREAM;  // use TCP
   hints.ai_flags = AI_PASSIVE;

   // call getaddrinfo() to update servInfo
   int error = getaddrinfo(server, port, &hints, &servInfo);
   if (error != 0)
   {
      cerr << "getaddrinfo() Error! " << error << endl;
      exit(1);
   }

   return createNewSocket(servInfo);
}

int TcpSocket::createNewSocket(addrinfo *servInfo)
{
   // make a socket, bind it, listen to it
   int sd = socket(servInfo->ai_family, servInfo->ai_socktype,
                   servInfo->ai_protocol);
   if (sd < 0)
   {
      cerr << "Socket creation error!" << errno << endl;

      return -1;
   }
   // lose pesky "Address already in use" error message
   const int yes = 1;
   if (setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, (char *)&yes, sizeof(yes)) < 0)
   {
      cerr << "Set Socket Option Error!" << endl;
   }

   // if no server given, this is a server, bind port, listen to it
   if (servInfo->ai_addrlen < 1)
   {
      if (bind(sd, servInfo->ai_addr, servInfo->ai_addrlen) < 0)
      {
         close(sd);
         cerr << "server: bind " << errno << endl;
         return -1;
      }
      if (listen(sd, MAX_REQUESTS) < 0)
      {
         cerr << "listen error" << errno << endl;
         close(sd);
         return -1;
      }
   }
   else
   { // client. connect to server
      int status = connect(sd, servInfo->ai_addr, servInfo->ai_addrlen);
      if (status < 0)
      {
         cerr << "Failed to connect to the server" << errno << endl;

         return -1;
      }
   }

   return sd;
}

int TcpSocket::send(char *msg, int msgSize)
{
   int totalBytesSent = 0;
   while (totalBytesSent < msgSize)
   {
      int bytesSent = write(sd, (char *)msg, msgSize);
      if (bytesSent < 0)
      {
         cerr << "SEND ERROR" << errno << endl;
         return -1;
      }
      else
      {
         totalBytesSent += bytesSent;
      }
   }

   return 0;
}
