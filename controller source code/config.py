import sys
from ncclient.xml_ import *
import xml.dom.minidom

def edit_cfg (cu, slots):
    #шаблон конфигурации
    cfg_str = '''          
                              <interfaces>
                                        <interface>
                                          <name>ce1-0/0/0</name>
                                             <partition>
                                               <name>1</name>
                                                 <timeslots>{}</timeslots>
                                                 <interface-type>ds</interface-type>
                                             </partition>
                                      </interface>
                              </interfaces>
                          '''.format(slots)
    cu.lock()                         #блокировка конфигурации
    cu.load(cfg_str, format='xml')    #загрузка новой конфигурации
    cu.pdiff()                        #вывод изменений
    cu.commit()                       #фиксация изменений
    cu.unlock()                       #разблокировка конфигурации