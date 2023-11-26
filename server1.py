import socket
import argparse
#版本1.0，添加了命令行参数，可以指定端口号，解析请求路径，返回文件内容

# HTTP响应头
def generate_headers(status_code):
    header = ''
    if status_code == 200:
        header += 'HTTP/1.1 200 OK\n'
    elif status_code == 404:
        header += 'HTTP/1.1 404 Not Found\n'

    header += 'Server: SimpleHTTPServer\n'
    header += 'Connection: close\n\n'

    return header

# 处理HTTP GET请求
def handle_get_request(request):
    # 解析请求路径
    filename = request.split(' ')[1]
    if filename == '/':
        filename = '/index.html'

    try:
        # 读取文件内容
        with open('files' + filename, 'rb') as f:
            content = f.read()
            response = generate_headers(200).encode() + content
    except FileNotFoundError:
        # 文件不存在
        response = generate_headers(404).encode()

    return response

# 处理HTTP请求
def handle_request(client_socket):
    # 接收客户端请求数据
    request_data = client_socket.recv(1024).decode()

    # 处理GET请求
    if request_data.startswith('GET'):
        response = handle_get_request(request_data)
    else:
        # 其他请求暂不处理
        response = generate_headers(404).encode()

    # 发送响应数据给客户端
    client_socket.sendall(response)

    # 关闭客户端连接
    client_socket.close()

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

    # 绑定IP和端口
    server_socket.bind((args.ip, args.port))

    # 监听客户端连接
    server_socket.listen(1)
    print('Server is running on http://{}:{}'.format(args.ip, args.port))

    while True:
        # 接受客户端连接
        client_socket, client_address = server_socket.accept()
        print('Client connected:', client_address)

        # 处理客户端请求
        handle_request(client_socket)

    # 关闭服务器套接字
    server_socket.close()

if __name__ == '__main__':
    main()
