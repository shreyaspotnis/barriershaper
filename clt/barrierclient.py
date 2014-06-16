import socket
import StringIO
import numpy as np

pre_command_length = 128
serverHost = 'elementu'
serverPort = 8001


def get_upload_string(addresses, values):
    ss = StringIO.StringIO()
    data_array = np.vstack((addresses, values)).T
    np.savetxt(ss, data_array, fmt='%d')
    return ss.getvalue()


def upload_points(addresses, values):
    sockobj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockobj.connect((serverHost, serverPort))

    send_string(sockobj, get_upload_string(addresses, values))

    return sockobj


def wait_before_closing_socket(sockobj, addresses, values):
    for i in range(len(addresses)):
        print(recv_string(sockobj))

    sockobj.close()


def send_string(sockobj, string):
    string_length = str(len(string)).ljust(pre_command_length)
    sockobj.send(string_length)
    sockobj.send(string)


def recv_string(sockobj):
    string_size = int(sockobj.recv(pre_command_length))
    received_size = 0
    data = []
    while(received_size < string_size):
        bytes_left = string_size - received_size
        curr_data = sockobj.recv(bytes_left)
        bytes_recvd = len(curr_data)
        data.append(curr_data)
        received_size += bytes_recvd
    return ''.join(data)
