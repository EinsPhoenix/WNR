from time import sleep, perf_counter

from pydobot import Dobot


try:
    device = Dobot(port="COM5", verbose=False)
    (x, y, z, r, j1, j2, j3, j4) = device.pose()
    # device.move_to(x + 20, y, z + 7, r, wait=True)
    # sleep(0.5)
    # device.move_to(x + 20, y, z, r, wait=True)
    # sleep(0.5)
    # device.move_to(x + 20, y, z + 7, r, wait=True)
    # sleep(0.5)
    # device.move_to(x, y, z, r, wait=True)
    device.move_to(x, y, z + 10, r, wait=True)
finally:
    device.close()