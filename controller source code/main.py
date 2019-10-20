from jnpr.junos import Device
from monitor import _get_info
from config import *
from jnpr.junos.utils.config import Config
from collections import deque
import sys
from datetime import datetime

###
#возвращает количество слотов для конфигурирования
#current - текущее кол-во слотов
#increase - флаг увеличения/уменьшения
###
def generate_count_of_slots(current, increase):
    slot_str = ['1', '1-2', '1-3', '1-4']

    index_now = int(slot_str.index(current))  #поиск положения текущего кол-ва слотов в массиве 
    if increase and index_now < 3:            #если необходимо увеличить и значение меньше максимального
        return slot_str[index_now+1]          #
    elif not increase and index_now > 1:      #если необходимо уменьшить и значение большн минимального
        return slot_str[index_now-1]
    else:
        return current

###
#возвращает количество слотов для конфигурирования
#log - информационное сообщение
#increase - флаг увеличения/уменьшения
###        
def change_slots(increase, log):
    global timeslots
    global max_speed
    global delay
    global log_file
    timeslots = generate_count_of_slots(timeslots, increase) #генерируем кол-во слотов
    edit_cfg(conf1, timeslots)                                 #изменяем конфигурацию устройств
    edit_cfg(conf2, timeslots)                                 #
    log = "{}, current {}\n".format(log, timeslots)          #генерируем информационное сообщение
    print(log)                                               #записываем в файл
    log_file.write(log)                                      #выводим на экран
    max_speed = 0                                            #обнуляем значение максимальной скорости передачи
    delay = 8                                                #устанавливает задержку перед последующим мониторингом

buf = deque()       #создаём очередь
buff_size = 7       #размер скользящего окна
delay = 8           #длительность задержки
max_speed = 0       #максимальная скорость передачи
diff_speed = 30000  #ограничение на разность максимальной и текущей скоростей передачи
max_avg = 20        #ограничение на среднее значение потерянных пакетов
timeslots = '1'     #начальное кол-во слотов

#подготовка log-файла
header = '{:27} {:29} {:12} {:7} {}'.format('monitoring:', 'buffer:', 'max speed:', 'diff:', 'average:')
log_file = open('log_{}.txt'.format(datetime.now().strftime('%d-%m-%Y_%H-%M-%S')), mode = 'w')
log_file.write(header + '\n')

#создание подключений к маршрутизаторам
dev1 = Device('10.10.10.9', user='login', passwd='password', port=830).open()
dev2 = Device('10.10.10.10', user='login', passwd='password', port=830).open()
conf1 = Config(dev1)
conf2 = Config(dev2)

#установка стартового состояния
edit_cfg(conf1, timeslots)
edit_cfg(conf2, timeslots)

try:    
    while(True):
        arr = _get_info(dev1)     #получаем данные маршрутизатора   
        
        if len(buf) == buff_size: #организуем работу очереди    
            buf.popleft()

        if len(arr) != 0:         #исключаем пустые массивы, которые возвращаются из внешней функции 
            buf.append(arr[2])    #наполняем буффер значениями  

        #организация паузы между изменениями конфигураций
        if delay > 0:
            delay -= 1
            print('\rPAUSE...{}'.format(delay), end = '')
            continue
        elif delay == 0:
            delay -= 1
            print('\n\n' + header)
        
        if len(buf) == buff_size:
            avg=sum(buf)/len(buf)  #вычисляем среднее значение потерянных пакетов
            speed = int(arr[1])    #запоминаем текущую скорость передачи
            
            if speed >= max_speed: #вычисляем максимальную скорость передачи
                max_speed = speed
            
            log = '{:27} {:29} {:12} {:7} {}'.format(str(arr), str(list(buf)), str(max_speed), str(max_speed-speed), str(round(avg, 3)))
            print(log)
            log_file.write(log + '\n')
                   
            #если кол-во потерянных пакетов превышает допустимое - увеличиваем кол-во слотов
            if avg > max_avg:
                print('\n***********************INCREASE***********************')
                change_slots(True, "+1 ts")
            
            #если максимальная скорость передачи больше текущей на diff_speed и потерь нет - уменьшаем кол-во слотов            
            elif (max_speed-speed >= diff_speed) and avg == 0:
                print('\n***********************DECREASE***********************')
                change_slots(False, "-1 ts")
except:
    print('\nExiting...')
finally:
    #закрываем подключения и сохраняем log-файл
    dev1.close()        
    dev2.close()
    log_file.close()
