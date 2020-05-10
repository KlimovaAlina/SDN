from jnpr.junos import Device

#form rpc request to a router
def rpc_get (dev):
    return dev.rpc.get_interface_information(
        detail=True, 
        interface_name='ds-0/0/0:1'
    )

#data request and processing
def _get_info (dev, old = 0):
    _filter = [
        '//speed',
        '//output-bps',
        '//queue[queue-number=0]/queue-counters-red-packets'
    ]
    old = int(rpc_get(dev).xpath(_filter[2])[0].text.strip())
    prev = int(rpc_get(dev).xpath(_filter[1])[0].text.strip())
    
    response = rpc_get(dev)
    out = []

    #save data to an array [interface speed, transfer rate, lost packets]
    for f in _filter:
        out.append(response.xpath(f)[0].text.strip()) 
      
    #save the number of lost packets after the previous request       
    div    = int(out[2])-old
    old    = int(out[2])
    out[2] = int(div)
    
    #skip duplicate data    
    if (prev != out[1]):
        prev = out[1]
        return out
    else:
        prev = out[1]
        return []
