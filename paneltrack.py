from pymodbus.client import ModbusTcpClient
import struct
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format with timestamp
    datefmt="%Y-%m-%d %H:%M:%S"  # Date format
)

class PaneltrackClient:
    register_map = {
        # Device and Version Information
        "Vab": {"start_address": 1, "length": 2, "type": "FLOAT32", "device_class": "voltage", "unit": "V"},
        "Vbc": {"start_address": 3, "length": 2, "type": "FLOAT32", "device_class": "voltage", "unit": "V"},
        "Vca": {"start_address": 5, "length": 2, "type": "FLOAT32", "device_class": "voltage", "unit": "V"},
        "Va": {"start_address": 7, "length": 2, "type": "FLOAT32", "device_class": "voltage", "unit": "V"},
        "Vb": {"start_address": 9, "length": 2, "type": "FLOAT32", "device_class": "voltage", "unit": "V"},
        "Vc": {"start_address": 11, "length": 2, "type": "FLOAT32", "device_class": "voltage", "unit": "V"},
        "Ia": {"start_address": 13, "length": 2, "type": "FLOAT32", "device_class": "current", "unit": "A"},
        "Ib": {"start_address": 15, "length": 2, "type": "FLOAT32", "device_class": "current", "unit": "A"},
        "Ic": {"start_address": 17, "length": 2, "type": "FLOAT32", "device_class": "current", "unit": "A"},
        "Pa": {"start_address": 19, "length": 2, "type": "FLOAT32", "device_class": "power", "unit": "W"},
        "Pb": {"start_address": 21, "length": 2, "type": "FLOAT32", "device_class": "power", "unit": "W"},
        "Pc": {"start_address": 23, "length": 2, "type": "FLOAT32", "device_class": "power", "unit": "W"},
        "Qa": {"start_address": 25, "length": 2, "type": "FLOAT32", "device_class": "reactive_power", "unit": "var"},
        "Qb": {"start_address": 27, "length": 2, "type": "FLOAT32", "device_class": "reactive_power", "unit": "var"},
        "Qc": {"start_address": 29, "length": 2, "type": "FLOAT32", "device_class": "reactive_power", "unit": "var"},
        "Sa": {"start_address": 31, "length": 2, "type": "FLOAT32", "device_class": "apparent_power", "unit": "VA"},
        "Sb": {"start_address": 33, "length": 2, "type": "FLOAT32", "device_class": "apparent_power", "unit": "VA"},
        "Sc": {"start_address": 35, "length": 2, "type": "FLOAT32", "device_class": "apparent_power", "unit": "VA"},
        "Pfa": {"start_address": 37, "length": 2, "type": "FLOAT32", "device_class": "power_factor", "unit": ""},
        "Pfb": {"start_address": 39, "length": 2, "type": "FLOAT32", "device_class": "power_factor", "unit": ""},
        "Pfc": {"start_address": 41, "length": 2, "type": "FLOAT32", "device_class": "power_factor", "unit": ""},
        "PSum": {"start_address": 43, "length": 2, "type": "FLOAT32", "device_class": "power", "unit": "W"},
        "QSum": {"start_address": 45, "length": 2, "type": "FLOAT32", "device_class": "reactive_power", "unit": "var"},
        "SSum": {"start_address": 47, "length": 2, "type": "FLOAT32", "device_class": "apparent_power", "unit": "VA"},
        "pfSum": {"start_address": 49, "length": 2, "type": "FLOAT32", "device_class": "power_factor", "unit": ""},
        "Freq": {"start_address": 51, "length": 2, "type": "FLOAT32", "device_class": "frequency", "unit": "Hz"},
        "MonthkWhTotal": {"start_address": 53, "length": 2, "type": "FLOAT32", "device_class": "energy", "unit": "kWh"},
        "DaykWhTotal": {"start_address": 55, "length": 2, "type": "FLOAT32", "device_class": "energy", "unit": "kWh"},
        "TotalImportEnergy": {"start_address": 57, "length": 2, "type": "INTEGER32", "state_class": "total_increasing", "device_class": "energy", "unit": "kWh"},
        "TotalExportEnergy": {"start_address": 59, "length": 2, "type": "INTEGER32", "state_class": "total_increasing", "device_class": "energy", "unit": "kWh"}
    }

    def __init__(self, ip_address, port=502):
        self.client = ModbusTcpClient(ip_address, port=port)

    def get_reg_map(self):
        return self.register_map

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()

    def read_register(self, meter_address, name):
        if name not in self.register_map:
            raise ValueError(f"Register '{name}' is not defined in the register map.")
        
        register = self.register_map[name]
        start_address = register["start_address"]
        length = register["length"]
        reg_type = register["type"]

        result = self.client.read_holding_registers(start_address-1, length, slave=meter_address)
        # result = self.client.read_input_registers(start_address, length, slave=1)
        if not result.isError():
            if reg_type == "FLOAT32":
                return round(self._decode_float32(result.registers), 2)
            elif reg_type == "INTEGER16":
                return result.registers[0]
            elif reg_type == "INTEGER32":
                return self._decode_int32(result.registers)
        else:
            logging.error(f"Error reading register '{name}': {result}")

    def _decode_float32(self, registers):
        raw = struct.pack('>HH', registers[0], registers[1])
        return struct.unpack('>f', raw)[0]

    def _decode_int32(self, registers):
        raw = struct.pack('>HH', registers[0], registers[1])
        return struct.unpack('>I', raw)[0]

# Example usage
if __name__ == "__main__":
    ip_address = "192.168.1.190"
    reader = PaneltrackClient(ip_address)
    
    if reader.connect():
        try:
            vab = reader.read_register("Vab")
            logging.info(f"Vab: {vab} V")

            va = reader.read_register("Va")
            logging.info(f"Va: {va} V")

            ia = reader.read_register("Ia")
            logging.info(f"Ia: {ia} A")

            pa = reader.read_register("Pa")
            logging.info(f"Pa: {pa} W")

            # More register reads as needed
        finally:
            reader.close()
    else:
        logging.error("Failed to connect to the Modbus server.")