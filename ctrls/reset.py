from smbus2 import SMBus
import time

DRV_ADD = 0x59

def slct_ctrl_pg(bus):
    bus.write_byte_data(DRV_ADD, 0xFF, 0x00)
    time.sleep(0.1)

def slct_mem_pg_1(bus):
    bus.write_byte_data(DRV_ADD, 0xFF, 0x01)
    time.sleep(0.1)

def reset(bus):
    slct_ctrl_pg(bus)
    bus.write_byte_data(DRV_ADD, 0x02, 0x80)
    time.sleep(0.1)
    #slct_mem_pg_1(bus)
    #bus.write_byte_data(DRV_ADD, 0x02, 0x80)




def main():
    with SMBus(7) as bus:
        reset(bus)
    print(f'device @ 0x{DRV_ADD} reset')


if __name__ == '__main__':
    main()