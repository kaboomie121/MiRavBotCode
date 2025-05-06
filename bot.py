import time

def test():
    test = 1
    while True:
        print(test)
        test += 1
        time.sleep(1)

print('hello!')

test()