#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <arpa/inet.h>
#include <sys/epoll.h>

#define PORT 9000
#define MAX_EVENTS 100
#define BUFFER_SIZE 2048
#define MAX_CLIENTS 1000

typedef struct {
    int fd;
    char id[50];
    int is_device;
} client_t;

client_t clients[MAX_CLIENTS];

int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

void send_to_device(const char *device_id, const char *msg) {
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].fd > 0 && clients[i].is_device && strcmp(clients[i].id, device_id) == 0) {
            send(clients[i].fd, msg, strlen(msg), 0);
            printf("Forwarded to %s: %s", device_id, msg);
            return;
        }
    }
    printf("Device %s not found.\n", device_id);
}

void broadcast_to_clients(const char *msg) {
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].fd > 0 && !clients[i].is_device) {
            send(clients[i].fd, msg, strlen(msg), 0);
        }
    }
}

int main() {
    int server_fd, epoll_fd;
    struct sockaddr_in addr;
    struct epoll_event ev, events[MAX_EVENTS];

    memset(clients, 0, sizeof(clients));

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    addr.sin_family = AF_INET;
    addr.sin_port = htons(PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));
    listen(server_fd, 10);
    set_nonblocking(server_fd);

    epoll_fd = epoll_create1(0);
    ev.events = EPOLLIN;
    ev.data.fd = server_fd;
    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, server_fd, &ev);

    printf("C TCP Server started on port %d\n", PORT);

    while (1) {
        int n = epoll_wait(epoll_fd, events, MAX_EVENTS, -1);
        for (int i = 0; i < n; i++) {
            if (events[i].data.fd == server_fd) {
                int client_fd = accept(server_fd, NULL, NULL);
                set_nonblocking(client_fd);
                
                ev.events = EPOLLIN | EPOLLET;
                ev.data.fd = client_fd;
                epoll_ctl(epoll_fd, EPOLL_CTL_ADD, client_fd, &ev);
                
                clients[client_fd].fd = client_fd;
                printf("New connection accepted, fd: %d\n", client_fd);
            } else {
                int fd = events[i].data.fd;
                char buffer[BUFFER_SIZE];
                int bytes = recv(fd, buffer, sizeof(buffer)-1, 0);

                if (bytes <= 0) {
                    close(fd);
                    printf("Client disconnected, fd: %d\n", fd);
                    memset(&clients[fd], 0, sizeof(client_t));
                } else {
                    buffer[bytes] = '\0';

                    // Parse incoming message format
                    if (strncmp(buffer, "REGISTER_DEVICE:", 16) == 0) {
                        sscanf(buffer, "REGISTER_DEVICE:%49s", clients[fd].id);
                        clients[fd].is_device = 1;
                        printf("Registered device: %s\n", clients[fd].id);
                    } else if (strncmp(buffer, "REGISTER_CLIENT", 15) == 0) {
                        clients[fd].is_device = 0;
                        printf("Registered web client bridge\n");
                    } else if (strncmp(buffer, "CMD:", 4) == 0) {
                        char username[50], device[50], action[50];
                        // format: CMD:username:device:action
                        if (sscanf(buffer, "CMD:%49[^:]:%49[^:]:%49s", username, device, action) == 3) {
                            printf("User '%s' commanded '%s' to turn %s\n", username, device, action);
                            
                            // 1. Send command strictly to the device
                            char msg[128];
                            snprintf(msg, sizeof(msg), "CMD:%s:%s\n", device, action);
                            send_to_device(device, msg);
                            
                            // 2. Broadcast system message so all web users know WHO fired the command
                            char sys_msg[128];
                            snprintf(sys_msg, sizeof(sys_msg), "SYS:User %s commanded %s to %s\n", username, device, action);
                            broadcast_to_clients(sys_msg);
                        }
                    } else if (strncmp(buffer, "STATUS:", 7) == 0) {
                        broadcast_to_clients(buffer);
                    }
                }
            }
        }
    }
    return 0;
}
