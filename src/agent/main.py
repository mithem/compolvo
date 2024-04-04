import time

def main():
    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)