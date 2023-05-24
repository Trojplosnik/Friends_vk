import base64
import socket
import json
import sys
import ssl
import re


API_VERSION = 5.131
with open("config.json") as json_file:
    file = json.load(json_file)
    ACCESS_TOKEN = file["access_token"]

METHOD_NAME = "friends.get"

SERVER_ADDR = "api.vk.com"
PORT = 443

ssl_contex = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_contex.check_hostname = False
ssl_contex.verify_mode = ssl.CERT_NONE

parameters = {
    "user_id": "",
    "order": "name",
    "name_case": "nom",
    "fields": "name"
}
regex = r'"id":(\d+).+?"first_name":"(.*?)","last_name":"(.*?)"'


def request(sock: ssl.SSLSocket, req: str) -> list[tuple[str, str, str]]:
    sock.send((req + '\n').encode())
    result = b""
    recv_data = sock.recv(12).decode("utf-8").split(" ")
    if recv_data[1] != "200":
        print(f"Network error: {recv_data[1]}")
        exit(1)
    while recv_data:
        recv_data = sock.recv(1024)
        result += recv_data
    friends = re.findall(regex, result.decode("utf-8"))
    if not friends:
        print('User has no friends :(')
    return friends


def prepare_message(data: dict) -> str:
    message = data["method"] + " " + data["url"]\
              + f" HTTP/{data['version_http']}\n"
    for header, value in data["headers"].items():
        message += f"{header}: {value}\n"
        message += "\n"
    if data["body"] is not None:
        message += data["body"]
    return message


def create_url(param: dict) -> str:
    url = f"/method/{METHOD_NAME}?"
    for name, value in param.items():
        url += f"{name}={value}&"
    url += f"access_token={ACCESS_TOKEN}&v={API_VERSION}"
    return url


def find_friends(user_id: str) -> list[tuple[str, str, str]]:
    parameters["user_id"] = user_id
    with socket.create_connection((SERVER_ADDR, PORT)) as sock:
        with ssl_contex.wrap_socket(sock, server_hostname=SERVER_ADDR)\
                as client:
            message = prepare_message(
                {
                    "method": "GET",
                    "url": create_url(parameters),
                    "version_http": "1.1",
                    "headers": {"HOST": SERVER_ADDR, "Accept": "*/*",
                                "Authorization":
                                    "Basic " +
                                    base64
                                    .b64encode(f"{ACCESS_TOKEN}"
                                               .encode()).decode()
                                },
                    "body": None
                }
            )
            return request(client, message)


def print_friends(friends: list[tuple[str, str, str]]):
    for number, friend in enumerate(friends):
        print(f"{number + 1}){friend[1]} {friend[2]}, ID: {friend[0]}")


def main():
    if len(sys.argv) == 2:
        print_friends(find_friends(sys.argv[1]))
    else:
        print("Wrong input: too many parameters")


if __name__ == '__main__':
    main()
