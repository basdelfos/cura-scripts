from ..Script import Script
import re
from UM.Application import Application
class FilamentAtHeight(Script):
    def __init__(self):
        super().__init__()
    
    def getSettingDataString(self):
        return """{
            "name":"Change filament at height",
            "key": "FilamentAtHeight",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pause_height":
                {
                    "label": "Height",
                    "description": "At what height should the filament change occur.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0
                }
            }
        }"""
    
    ##  Convenience function that finds the value in a line of g-code.
    #   When requesting key = x from line "G1 X100" the value 100 is returned.
    #   Override original function, which didn't handle values without a leading zero like ".3"
    def getValue(self, line, key, default = None):
        if not key in line or (';' in line and line.find(key) > line.find(';')):
            return default
        sub_part = line[line.find(key) + 1:]
        m = re.search('^[0-9]+\.?[0-9]*', sub_part)
        if m is None:
            m = re.search('^[0-9]*\.?[0-9]+', sub_part)
        if m is None:
            return default
        try:
            return float(m.group(0))
        except:
            return default
    
    def execute(self, data):
        x = 0.
        y = 0.
        last_e = 0.
        current_z = 0.
        pause_z = self.getSettingValueByKey("pause_height")
        layers_started = False
        
        for layer in data:
            lines = layer.split("\n")
            for line in lines:
                if not layers_started:
                    if ";LAYER:0" in line:
                        layers_started = True
                    continue
                e = self.getValue(line, "E")
                if e is not None and e > last_e:
                    last_e = e
                g = self.getValue(line, "G")
                if g == 1 or g == 0:
                    x = self.getValue(line, "X")
                    y = self.getValue(line, "Y")
                    current_z = self.getValue(line, "Z")
                    if current_z is not None and x is not None and y is not None:
                        if current_z >= pause_z:
                            data_index = data.index(layer)
                            line_index = lines.index(line)
                            
                            prepend_gcode = ";TYPE:CUSTOM\n"
                            prepend_gcode += ";added code by post processing\n"
                            prepend_gcode += ";script: FilamentAtHeight.py\n"
                            prepend_gcode += ";current z: %f\n" % (current_z)
                            
                            prepend_gcode += "M600 E-5.0 X0.0 Y0.0 Z5   ; change filament\n"
                            
                            beginning = lines[:line_index]
                            ending = lines[line_index:]
                            layer = "\n".join(beginning) + "\n" + prepend_gcode + "\n".join(ending) + "\n"
                            
                            data[data_index] = layer #Override the data of this layer with the modified data
                            
                            #We're done
                            return data
                        continue
                
        return data
