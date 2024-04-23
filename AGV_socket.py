import socket
import time

# 호스트와 포트 설정
host = '192.168.0.7'  # 서버의 IP 주소
# host = '172.20.10.13'
port = 23451       # 사용할 포트 번호

# 소켓 생성
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 소켓을 지정된 호스트와 포트에 바인딩
server_socket.connect((host, port))

# # 클라이언트 연결 대기
# server_socket.listen(5)
# print(f"서버가 {host}:{port}에서 대기 중입니다...")

# # 클라이언트 연결 수락
# client_socket, client_address = server_socket.accept()
# print(f"{client_address}에서 연결되었습니다.")

# 클라이언트와 통신
while True:
    # 클라이언트로부터 메시지 수신
    while True:
        # 사용자에게 문자열 입력 받아 클라이언트로 전송
        message_to_send_input = 'Start'
        server_socket.send(message_to_send_input.encode())
        data = server_socket.recv(1024).decode()
        print(data[-1])
        if data=='Y':
            print(f"서버로부터 받은 메시지1: {data[-1]}")
            break

        print(f"서버로부터 받은 메시지2: {data[-1]}")
        time.sleep(0.5)

    # 사용자에게 문자열 입력 받아 클라이언트로 전송
    CM = 30
    message_to_send = f'AGR/GO/{CM}'
    server_socket.send(message_to_send.encode())
    break

# 연결 종료
# client_socket.close()
server_socket.close()