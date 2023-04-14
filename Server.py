import socket
import threading
import time
import random
import pickle


class Snake:
    color = None
    body = []
    direction = [0, 0]

    def __init__(self, x, y, direction, color):
        self.body = [[x, y]]
        self.direction = direction
        self.color = color

    def set_direction(self, direction):
        self.direction = direction

    def move(self):
        new_x = self.body[-1][0] + self.direction[0]
        new_y = self.body[-1][1] + self.direction[1]
        if new_x < 0 or new_x > 35:
            new_x = (new_x + 36) % 36
        if new_y < 0 or new_y > 23:
            new_y = (new_y + 24) % 24
        self.body.append([new_x, new_y])
        changes.append([[new_x, new_y], self.color])
        for position in food_positions:
            if self.body[-1] == position:
                create_food()
                delete_food(position)
                break
        else:
            x, y = self.body.pop(0)
            changes.append([[x, y], BLACK])


def create_food():
    while True:
        x = random.randrange(36)
        y = random.randrange(24)
        if [x, y] not in snake_P1.body and [x, y] not in snake_P2.body and [x, y] not in food_positions:
            changes.append([[x, y], GREEN])
            food_positions.append([x, y])
            break


def delete_food(position):
    food_positions.remove(position)


def detect_collision():
    p1_die = False
    p2_die = False
    if snake_P1.body[-1] in snake_P1.body[:-1] or snake_P1.body[-1] in snake_P2.body:
        p1_die = True
    if snake_P2.body[-1] in snake_P2.body[:-1] or snake_P2.body[-1] in snake_P1.body:
        p2_die = True
    if p1_die and p2_die:
        if len(snake_P1.body) > len(snake_P2.body):
            result = [True, 2, "Red win"]
        elif len(snake_P1.body) == len(snake_P2.body):
            result = [True, 2, "Draw"]
        else:
            result = [True, 2, "Blue win"]
    elif p1_die:
        result = [True, 1, "Blue win"]
    elif p2_die:
        result = [True, 1, "Red win"]
    else:
        result = [False]
    if result[0]:
        changes.append(["end", result[1], result[2]])
    return result


def detect_length():
    if len(snake_P1.body) == 20 and len(snake_P2.body) == 20:
        result = [True, 3, "Draw"]
    elif len(snake_P1.body) == 20:
        result = [True, 3, "Red win"]
    elif len(snake_P2.body) == 20:
        result = [True, 3, "Blue win"]
    else:
        result = [False]
    if result[0]:
        changes.append(["end", result[1], result[2]])
    print(len(snake_P1.body), len(snake_P2.body), result)
    return result


def receive(client_socket, user_code):
    while Game_in_progress:
        data = client_socket.recv(BUFSIZ)
        data = data.decode('utf-8')
        print("user %d - %s" % (user_code, data))
        if data == "left":
            data = LEFT
        elif data == "right":
            data = RIGHT
        elif data == "up":
            data = UP
        elif data == "down":
            data = DOWN
        elif data == "quit":
            users.remove(users[user_code - 1])
            if user_code == 1:
                winner = "Blue win"
            else:
                winner = "Red win"
            changes.append(["quit", winner])
            send_changes()
            break
        else:
            data = [0, 0]
        body = snakes[user_code - 1].body
        if len(body) == 1 or not (len(body) > 1 and body[-1][0] - body[-2][0] + data[0] == 0
                                  and body[-1][1] - body[-2][1] + data[1] == 0):
            snakes[user_code - 1].direction = data


def send_changes():
    data = pickle.dumps(changes)
    for client_socket in users:
        client_socket[0].send(data)


HOST = "172.30.1.49"
PORT = 9999
BUFSIZ = 1024

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(2)

users = []
food_positions = []
LEFT = [-1, 0]
RIGHT = [1, 0]
UP = [0, 1]
DOWN = [0, -1]

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
changes = []

Game_in_progress = True

while len(users) < 2:
    print("Waiting for Connection...")
    client_socket, address = server_socket.accept()
    users.append([client_socket, len(users) + 1])
    usr_code = len(users)
    client_socket.send(str(usr_code).encode('utf-8'))
    print("Connection from %s, %s.(Currently %d user(s))" % (address[0], address[1], len(users)))

snake_P1 = Snake(6, 12, RIGHT, RED)
snake_P2 = Snake(30, 12, LEFT, BLUE)

def main():
    time.sleep(3)
    global snakes
    global Game_in_progress
    global changes
    global snake_P1
    global snake_P2
    global food_positions

    Game_in_progress = True
    threads = []
    food_positions = []
    changes = []
    snake_P1 = Snake(6, 12, RIGHT, RED)
    snake_P2 = Snake(30, 12, LEFT, BLUE)
    snakes = [snake_P1, snake_P2]

    for client_socket in users:
        receive_thread = threading.Thread(target=receive, args=(client_socket[0], client_socket[1]))
        threads.append(receive_thread)
        receive_thread.start()

    for _ in range(4):
        create_food()
    print("creation food")

    while True:
        time.sleep(0.1)
        snake_P1.move()
        snake_P2.move()
        print("snake moving")
        result = detect_collision()
        if result[0]:
            send_changes()
            break
        print("detecting collision")
        result = detect_length()
        if result[0]:
            send_changes()
            break
        print("detecting length")
        print(changes)
        if len(changes) > 0:
            send_changes()
        changes = []

    Game_in_progress = False

    for thread in threads:
        thread.join()
    print("every thread finish")


while True:
    main()
    yes_count = 0
    for client_socket in users:
        while True:
            data = client_socket[0].recv(BUFSIZ)
            data = data.decode('utf-8')
            print(data)
            if data == "No" or data == "Yes" or data == "doneYes" or data == "doneNo":
                break
        if data == "Yes" or data == "doneYes":
            yes_count += 1
    if yes_count == 2:
        for client_socket in users:
            client_socket[0].send("Yes".encode('utf-8'))
    else:
        for client_socket in users:
            client_socket[0].send("No".encode('utf-8'))
        break


server_socket.close()
for client_socket in users:
    client_socket[0].close()
