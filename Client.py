import socket
import threading
import pygame
import pickle
import tkinter
from tkinter import messagebox
import time


def sorting_by_priority(x):
    if x[0] == "quit":
        return 0
    elif x[0] == "end":
        return 1
    elif x[1] == BLACK:
        return 2
    else:
        return 3


def receive(client_socket):
    global changes
    while Game_in_progress:
        data = client_socket.recv(BUFSIZ)
        data = pickle.loads(data)
        if len(data) > 0:
            data.sort(key=sorting_by_priority)
            print(data)
            if data[0][0] == "end" or data[0][0] == "quit":
                end_game(data[0])
                break
            lock.acquire()
            changes += data
            lock.release()


def draw_screen(width, height, square_size, screen):
    x = 0
    y = 0
    for _ in range(width // square_size):
        x += square_size
        pygame.draw.line(screen, WHITE, (x, 0), (x, width))
    for _ in range(height // square_size):
        y += square_size
        pygame.draw.line(screen, WHITE, (0, y), (width, y))


def end_game(information):
    global Game_in_progress
    global Game_Result
    print("game has done", information)
    if information[0] == "quit":
        Game_Result = [information[1], "escape of opponent"]
        Game_in_progress = False
        return
    end_type = information[1]
    winner = information[2]
    if end_type == 1:
        reason = "collision"
    elif end_type == 2:
        reason = "length comparison"
    else:
        reason = "achieving goal length"
    Game_Result = [winner, reason]
    Game_in_progress = False


Game_in_progress = True
Game_Result = None

HOST = '172.30.1.49'
PORT = 9999
BUFSIZ = 1024

pygame.init()
width = 1080
height = 720
square_size = 30
FPS = 60
USR_CODE = 0

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

root = tkinter.Tk()
root.withdraw()

screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
clock.tick(FPS)
pygame.display.set_caption("Snake vs Snake")

draw_screen(width, height, square_size, screen)
pygame.display.flip()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
data = client_socket.recv(BUFSIZ)
usr_code = data.decode('utf-8')
print(usr_code)
if usr_code == "1":
    usr_position = 195
else:
    usr_position = 915

changes = []
lock = threading.Lock()

def main():
    global Game_in_progress
    global changes
    screen.fill(BLACK)
    draw_screen(width, height, square_size, screen)

    pygame.draw.rect(screen, RED, [181, 361, 29, 29])
    pygame.draw.rect(screen, BLUE, [901, 361, 29, 29])

    Game_in_progress = True
    receive_thread = threading.Thread(target=receive, args=(client_socket,))
    receive_thread.start()
    print("thread...OK")

    pygame.draw.polygon(screen, YELLOW, [[usr_position - 10, 335], [usr_position, 355], [usr_position + 10, 335]])
    pygame.display.flip()
    time.sleep(3)
    pygame.draw.rect(screen, BLACK, [usr_position - 14, 331, 29, 29])
    pygame.display.flip()

    while Game_in_progress:
        draw_screen(width, height, square_size, screen)
        lock.acquire()
        while changes:
            change = changes.pop()
            pygame.draw.rect(screen, change[1], [change[0][0]*30 + 1, change[0][1]*30 + 1, 29, 29])
        lock.release()
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client_socket.send("quit".encode('utf-8'))
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    print("left")
                    client_socket.send("left".encode('utf-8'))
                elif event.key == pygame.K_RIGHT:
                    print("right")
                    client_socket.send("right".encode('utf-8'))
                elif event.key == pygame.K_DOWN:
                    print("up")
                    client_socket.send("up".encode('utf-8'))
                elif event.key == pygame.K_UP:
                    print("down")
                    client_socket.send("down".encode('utf-8'))

    receive_thread.join()


while True:
    main()
    client_socket.send("done".encode('utf-8'))
    if Game_Result[1] == "escape of opponent":
        tkinter.messagebox.showinfo("Result", "%s by %s" % (Game_Result[0], Game_Result[1]))
        break
    else:
        answer = tkinter.messagebox.askyesno(" Result", "%s by %s \n will you play again? " % (Game_Result[0], Game_Result[1]))
        if answer:
            client_socket.send("Yes".encode('utf-8'))
            data = client_socket.recv(BUFSIZ)
            data = data.decode('utf-8')
            print(data)
            if data == "No":
                tkinter.messagebox.showinfo("Result", "Opponent has quit")
                break
        else:
            client_socket.send("No".encode('utf-8'))
            data = client_socket.recv(BUFSIZ)
            data.decode('utf-8')
            print(data)
            break

client_socket.close()
