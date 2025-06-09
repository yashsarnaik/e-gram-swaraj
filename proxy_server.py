#!/usr/bin/env python3
"""
Simple HTTP Proxy Server that modifies headers to make requests appear as localhost
"""

import socket
import threading
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LocalhostProxy:
    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        
    def start(self):
        """Start the proxy server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"Proxy server started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    logger.debug(f"Connection from {addr}")
                    
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Socket error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error starting proxy server: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the proxy server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
                logger.info("Proxy server stopped")
            except:
                pass
    
    def handle_client(self, client_socket):
        """Handle individual client connections"""
        try:
            # Receive the request
            request = client_socket.recv(4096).decode('utf-8')
            if not request:
                return

            logger.debug(f"Original request:\n{request[:500]}...")

            # Parse the request
            first_line = request.split('\n')[0]
            method = first_line.split(' ')[0]
            url = first_line.split(' ')[1]

            # Handle HTTPS CONNECT requests differently
            if method == 'CONNECT':
                self.handle_https_connect(client_socket, url)
                return

            # Extract host and port from the request
            http_pos = url.find("://")
            if http_pos == -1:
                temp = url
            else:
                temp = url[(http_pos + 3):]

            port_pos = temp.find(":")
            webserver_pos = temp.find("/")
            if webserver_pos == -1:
                webserver_pos = len(temp)

            if port_pos == -1 or webserver_pos < port_pos:
                port = 80
                webserver = temp[:webserver_pos]
            else:
                port = int(temp[(port_pos + 1):webserver_pos])
                webserver = temp[:port_pos]

            # Modify the request headers to appear as localhost
            modified_request = self.modify_headers(request)
            logger.debug(f"Modified request:\n{modified_request[:500]}...")

            # Connect to the target server
            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_socket.connect((webserver, port))
            proxy_socket.send(modified_request.encode('utf-8'))

            # Relay data between client and server
            while True:
                data = proxy_socket.recv(4096)
                if len(data) > 0:
                    client_socket.send(data)
                else:
                    break

        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            try:
                client_socket.close()
                if 'proxy_socket' in locals():
                    proxy_socket.close()
            except:
                pass

    def handle_https_connect(self, client_socket, url):
        """Handle HTTPS CONNECT requests for SSL tunneling"""
        try:
            # Parse host and port from CONNECT request
            if ':' in url:
                webserver, port = url.split(':')
                port = int(port)
            else:
                webserver = url
                port = 443

            logger.debug(f"HTTPS CONNECT to {webserver}:{port}")

            # Connect to the target server
            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_socket.connect((webserver, port))

            # Send 200 Connection established response
            client_socket.send(b"HTTP/1.1 200 Connection established\r\n\r\n")

            # Start bidirectional data relay
            self.relay_data(client_socket, proxy_socket)

        except Exception as e:
            logger.error(f"Error handling HTTPS CONNECT: {e}")
            try:
                client_socket.send(b"HTTP/1.1 500 Connection failed\r\n\r\n")
            except:
                pass
        finally:
            try:
                if 'proxy_socket' in locals():
                    proxy_socket.close()
            except:
                pass

    def relay_data(self, client_socket, server_socket):
        """Relay data bidirectionally between client and server"""
        import select

        try:
            while True:
                # Use select to handle bidirectional communication
                ready_sockets, _, _ = select.select([client_socket, server_socket], [], [], 1)

                if not ready_sockets:
                    continue

                for sock in ready_sockets:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            return

                        if sock is client_socket:
                            # Data from client to server
                            server_socket.send(data)
                        else:
                            # Data from server to client
                            client_socket.send(data)
                    except:
                        return

        except Exception as e:
            logger.debug(f"Relay ended: {e}")
        finally:
            try:
                client_socket.close()
                server_socket.close()
            except:
                pass
    
    def modify_headers(self, request):
        """Modify request headers to appear as localhost"""
        lines = request.split('\n')
        modified_lines = []
        
        # Headers to add/modify for localhost appearance
        localhost_headers = {
            'X-Forwarded-For': '127.0.0.1',
            'X-Real-IP': '127.0.0.1',
            'X-Forwarded-Host': 'localhost',
            'X-Forwarded-Proto': 'http',
            'X-Forwarded-Port': '80',
            'X-Original-Host': 'localhost',
            'Remote-Addr': '127.0.0.1',
            'Client-IP': '127.0.0.1'
        }
        
        # Process existing headers
        headers_added = set()
        for line in lines:
            if ':' in line and line.strip():
                header_name = line.split(':')[0].strip().lower()
                
                # Replace User-Agent with a localhost-like one
                if header_name == 'user-agent':
                    modified_lines.append('User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                    headers_added.add('user-agent')
                # Replace or modify other headers
                elif header_name in ['x-forwarded-for', 'x-real-ip', 'x-forwarded-host', 'x-forwarded-proto', 'x-forwarded-port', 'x-original-host', 'remote-addr', 'client-ip']:
                    # Replace with localhost values
                    for key, value in localhost_headers.items():
                        if key.lower() == header_name:
                            modified_lines.append(f'{key}: {value}')
                            headers_added.add(key.lower())
                            break
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        # Add missing localhost headers
        for key, value in localhost_headers.items():
            if key.lower() not in headers_added:
                # Insert before the empty line that separates headers from body
                for i, line in enumerate(modified_lines):
                    if line.strip() == '':
                        modified_lines.insert(i, f'{key}: {value}')
                        break
                else:
                    # If no empty line found, add before the last line
                    modified_lines.insert(-1, f'{key}: {value}')
        
        return '\n'.join(modified_lines)

def start_proxy_server(host='127.0.0.1', port=8888):
    """Start the proxy server in a separate thread"""
    proxy = LocalhostProxy(host, port)
    proxy_thread = threading.Thread(target=proxy.start)
    proxy_thread.daemon = True
    proxy_thread.start()
    
    # Give the server a moment to start
    time.sleep(1)
    
    return proxy

if __name__ == "__main__":
    # Test the proxy server
    proxy = LocalhostProxy()
    try:
        proxy.start()
    except KeyboardInterrupt:
        logger.info("Shutting down proxy server...")
        proxy.stop()
