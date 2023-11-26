import base64
import mimetypes
import os
import socket
import argparse
import time
import threading

# HTTP响应头
def generate_headers(status_code, content_length=0, content_type='', keep_alive=False):
    header = ''
    if status_code == 200:
        header += 'HTTP/1.1 200 OK\r\n'
    elif status_code == 400:
        header += 'HTTP/1.1 400 Bad Request\r\n'
    elif status_code == 404:
        header += 'HTTP/1.1 404 Not Found\r\n'
    elif status_code == 405:
        header += 'HTTP/1.1 405 Method Not Allowed\r\n'

    header += 'Server: SimpleHTTPServer\r\n'
    header += 'Connection: {}\r\n'.format('keep-alive' if keep_alive else 'close')
    header += 'Content-Length: {}\r\n'.format(content_length)
    header += 'Content-Type: {}\r\n'.format(content_type)

    header += '\r\n'
    return header

# 处理文件和目录的查看请求
def handle_get_request(request):
    # 解析请求路径
    path = request.split(' ')[1]
    if path == '/':
        path = '/index.html'

    # 拼接文件或目录的绝对路径
    abs_path = os.path.join('data', path[1:])

    # 检查路径是否存在
    if not os.path.exists(abs_path):
        response = generate_headers(404).encode()
        return response

    # 如果是目录，则列出目录下的文件和子目录
    if os.path.isdir(abs_path):
        content = '<html><body>'
        content += '<h1>Directory listing for {}</h1>'.format(path)
        content += '<ul>'
        # 列出文件
        for file_name in os.listdir(abs_path):
            file_path = os.path.join(abs_path, file_name)
            if os.path.isfile(file_path):
                content += '<li><a href="{}/{}">{}</a></li>'.format(path, file_name, file_name)
        # 列出子目录
        for dir_name in os.listdir(abs_path):
            dir_path = os.path.join(abs_path, dir_name)
            if os.path.isdir(dir_path):
                content += '<li><a href="{}/">{}/</a></li>'.format(os.path.join(path, dir_name), dir_name)
        content += '</ul>'
        content += '</body></html>'

        response = generate_headers(200, len(content), mimetypes.guess_type(abs_path)[0], True).encode() + content.encode()
    else:
        # 如果是文件，则返回文件内容
        with open(abs_path, 'rb') as f:
            content = f.read()
        response = generate_headers(200, len(content), mimetypes.guess_type(abs_path)[0], True).encode() + content

    return response

# 处理文件下载请求
def handle_post_request(request):
    # 解析请求路径
    path = request.split(' ')[1]
    if path == '/':
        path = '/index.html'

    # 拼接文件的绝对路径
    abs_path = os.path.join('data', path[1:])

    # 检查路径是否存在
    if not os.path.exists(abs_path):
        response = generate_headers(404).encode()
        return response

    # 如果是文件，则返回文件内容
    if os.path.isfile(abs_path):
        with open(abs_path, 'rb') as f:
            content = f.read()
        response = generate_headers(200, len(content), True).encode() + content
    else:
        response = generate_headers(404).encode()

    return response

# 检查用户认证信息
def check_authorization(request_data):
    headers = request_data.split('\n')
    for header in headers:
        if header.startswith('Authorization:'):
            authorization = header.split(':')[1].strip().split()
            if authorization[0].lower() == 'basic':
                encoded_info = authorization[1]
                decoded_info = base64.b64decode(encoded_info).decode()
                username, password = decoded_info.split(':')

                # 读取用户信息文件
                with open('users.txt', 'r') as f:
                    for line in f:
                        stored_username, stored_password = line.strip().split(':')
                        # 检查用户名和密码是否正确
                        if username == stored_username and password == stored_password:
                            return True
    return False

# 处理HTTP请求
def handle_request(client_socket):
    # 接收客户端请求数据
    request_data = client_socket.recv(1024).decode()

    while request_data:
        # 解析请求头部中的Connection字段
        connection = 'close'
        headers = request_data.split('\n')
        for header in headers:
            if header.startswith('Connection:'):
                connection = header.split(':')[1].strip().lower()
                break

        # 检查认证信息
        if not check_authorization(request_data):
            # 未提供认证信息或认证信息错误，返回401 Unauthorized
            response = generate_headers(401).encode()
        else:
            # 处理GET请求
            if request_data.startswith('GET'):
                response = handle_get_request(request_data)
            # 处理HEAD请求
            elif request_data.startswith('HEAD'):
                response = generate_headers(200, 0, connection == 'keep-alive').encode()
            # 处理POST请求
            elif request_data.startswith('POST'):
                response = handle_post_request(request_data)
            else:
                # 其他请求暂不处理
                response = generate_headers(404).encode()

        # 发送响应数据给客户端
        client_socket.sendall(response)

        # 关闭连接或继续接收请求
        if connection == 'close':
            break
        else:
            request_data = client_socket.recv(1024).decode()

    # 关闭客户端连接
    client_socket.close()
    
# 处理客户端连接
def handle_client(client_socket):
    try:
        # 处理客户端请求
        handle_request(client_socket)
    except Exception as e:
        print('Error handling client request:', e)

# 主函数
def main():
    # 创建解析器
    parser = argparse.ArgumentParser(description='Simple HTTP Server')
    parser.add_argument('-i', '--ip', type=str, default='localhost', help='Server IP address')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Server port number')

    # 解析命令行参数
    args = parser.parse_args()

    # 创建TCP套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 设置端口复用，服务器程序退出后可以立即重启
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 绑定IP和端口
    server_socket.bind((args.ip, args.port))

    # 监听客户端连接
    server_socket.listen(5)
    print('Server is running on http://{}:{}'.format(args.ip, args.port))

    while True:
        # 接受客户端连接
        client_socket, client_address = server_socket.accept()
        print('Client connected:', client_address)

        # 创建线程处理客户端请求
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

    # 关闭服务器套接字
    server_socket.close()

if __name__ == '__main__':
    main()