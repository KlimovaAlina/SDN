from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from collections import deque
import sys
from datetime import datetime
import time


def get_rpc(device, vlan):
    return device.rpc.get_interface_information(
        detail=True,
        interface_name=f'fe-1/3/0.{vlan}'
    )


def get_interface_speed(device, vlan, filter) -> float:
    rpc = get_rpc(device, vlan)
    return int(rpc.xpath(filter)[0].text.strip())/1000


if __name__ == '__main__':

    #создание подключений к маршрутизаторам
    dev1 = Device('10.10.10.9', user='login', passwd='password', port=830).open()
    dev2 = Device('10.10.10.10', user='login', passwd='password', port=830).open()
    conf1 = Config(dev1)

    data = ['./service', './voip_stat', './voip_dyn']
    current = None
    candidate = None

    log_file = open('with_{}.csv'.format(datetime.now().strftime('%d-%m-%Y_%H-%M-%S')), mode = 'w')

    seconds = 0

    try:
        while(True):

            voip_source = get_interface_speed(dev1, '11', '//input-bps')
            voip_receive = get_interface_speed(dev2, '12', '//output-bps')
            voip_drop = voip_source-voip_receive
            service_source = get_interface_speed(dev1, '14', '//input-bps')
            service_receive = get_interface_speed(dev2, '15', '//output-bps')
            service_drop = service_source-service_receive

            log = f'{seconds},{voip_receive},{voip_drop},{service_receive},{service_drop}'
            log_file.write(log + '\n')
            print(log)

            current = candidate

            if voip_source < 10:
                candidate = data[0]
            elif voip_source < 120:
                candidate = data[1]
            else:
                candidate = data[2]


            if current != candidate:
                conf1.lock()                         #блокировка конфигурации
                conf1.load(                          #загрузка новой конфигурации
                    format='text',
                    template_path=candidate,
                    template_vars={'vlan': 14},
                    ignore_warning='statement not found')
                conf1.pdiff()                        #вывод изменений
                conf1.commit()                       #фиксация изменений
                conf1.unlock()                       #разблокировка конфигурации

            seconds += 1

    except Exception as ex:
        print(f'{ex}\nExit')
    finally:
        dev1.close()
        dev2.close()
        log_file.close()
