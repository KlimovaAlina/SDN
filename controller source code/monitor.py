from jnpr.junos import Device

#формируем rpc запрос к маршрутизатору
def rpc_get (dev):
    return dev.rpc.get_interface_information(detail=True, interface_name='ds-0/0/0:1')

#запрос данных и их обработка
def _get_info (dev, old = 0):
    _filter = ['//speed', '//output-bps', '//queue[queue-number=0]/queue-counters-red-packets']
    old = int(rpc_get(dev).xpath(_filter[2])[0].text.strip())
    prev = int(rpc_get(dev).xpath(_filter[1])[0].text.strip())
    
    response = rpc_get(dev)
    out = []

    for f in _filter:
        out.append(response.xpath(f)[0].text.strip()) #сохраняем данные в массив [скорость интерфейса, скорость передачи, потерянные пакеты]
      
    #сохраняем кол-во потерянных пакетов после предыдущего запроса       
    div    = int(out[2])-old
    old    = int(out[2])
    out[2] = int(div)
    
    #пропускаем повторяющиеся данные    
    if (prev != out[1]):
        prev = out[1]
        return out
    else:
        prev = out[1]
        return []