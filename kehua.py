from pymodbus.client import ModbusTcpClient
import struct

class KehuaClient:
    register_map = {
        # Device and Version Information
        "Device Model": {"start_address": 4800, "length": 10, "type": "ASCII"},
        "Hardware Version": {"start_address": 4810, "length": 5, "type": "ASCII"},
        "Software Version": {"start_address": 4815, "length": 5, "type": "ASCII"},
        "HMI Version": {"start_address": 4820, "length": 5, "type": "ASCII"},
        "Manufacturer Info": {"start_address": 4825, "length": 15, "type": "ASCII"},
        
        # Operational Status
        "Running Status": {"start_address": 5001, "type": "UINT16"},
        "Fault Code 1": {"start_address": 5002, "type": "UINT16"},
        "Fault Code 2": {"start_address": 5003, "type": "UINT16"},
        "Fault Code 3": {"start_address": 5004, "type": "UINT16"},
        "Fault Code 4": {"start_address": 5005, "type": "UINT16"},
        
        # Grid and Output Voltages
        "Grid Voltage U": {"start_address": 5006, "type": "UINT16", "scale": 0.1, "unit": "V"},
        "Grid Voltage V": {"start_address": 5007, "type": "UINT16", "scale": 0.1, "unit": "V"},
        "Grid Voltage W": {"start_address": 5008, "type": "UINT16", "scale": 0.1, "unit": "V"},
        "Output Voltage U": {"start_address": 5009, "type": "UINT16", "scale": 0.1, "unit": "V"},
        "Output Voltage V": {"start_address": 5010, "type": "UINT16", "scale": 0.1, "unit": "V"},
        "Output Voltage W": {"start_address": 5011, "type": "UINT16", "scale": 0.1, "unit": "V"},
        
        # Output Currents
        "Output Current U": {"start_address": 5012, "type": "UINT16", "scale": 0.1, "unit": "A"},
        "Output Current V": {"start_address": 5013, "type": "UINT16", "scale": 0.1, "unit": "A"},
        "Output Current W": {"start_address": 5014, "type": "UINT16", "scale": 0.1, "unit": "A"},
        
        # Frequencies
        "Off-Grid Frequency": {"start_address": 5015, "type": "UINT16", "scale": 0.01, "unit": "Hz"},
        "Grid Frequency": {"start_address": 5016, "type": "UINT16", "scale": 0.01, "unit": "Hz"},
        
        # Temperatures
        "Inner Temperature": {"start_address": 5018, "type": "INT16", "scale": 0.1, "unit": "°C"},
        "Radiator Temperature": {"start_address": 5019, "type": "INT16", "scale": 0.1, "unit": "°C"},
        
        # DC and Power Information
        "DC Voltage": {"start_address": 5020, "type": "UINT16", "scale": 0.1, "unit": "V"},
        "DC Current": {"start_address": 5021, "type": "INT16", "scale": 0.1, "unit": "A"},
        "Total DC Power": {"start_address": 5022, "type": "INT16", "scale": 0.1, "unit": "kW"},
        "Output Apparent Power": {"start_address": 5023, "type": "UINT16", "scale": 0.1, "unit": "kVA"},
        "Output Active Power": {"start_address": 5024, "type": "INT16", "scale": 0.1, "unit": "kW"},
        "Output Reactive Power": {"start_address": 5025, "type": "INT16", "scale": 0.1, "unit": "kVar"},
        
        # Per-Phase Power Details
        "Phase-U Apparent Power": {"start_address": 5026, "type": "UINT16", "scale": 0.1, "unit": "kVA"},
        "Phase-U Active Power": {"start_address": 5027, "type": "INT16", "scale": 0.1, "unit": "kW"},
        "Phase-U Power Factor": {"start_address": 5028, "type": "INT16", "scale": 0.01},
        "Phase-U Load Capacity": {"start_address": 5029, "type": "UINT16", "unit": "%"},
        
        "Phase-V Apparent Power": {"start_address": 5030, "type": "UINT16", "scale": 0.1, "unit": "kVA"},
        "Phase-V Active Power": {"start_address": 5031, "type": "INT16", "scale": 0.1, "unit": "kW"},
        "Phase-V Power Factor": {"start_address": 5032, "type": "INT16", "scale": 0.01},
        "Phase-V Load Capacity": {"start_address": 5033, "type": "UINT16", "unit": "%"},
        
        "Phase-W Apparent Power": {"start_address": 5034, "type": "UINT16", "scale": 0.1, "unit": "kVA"},
        "Phase-W Active Power": {"start_address": 5035, "type": "INT16", "scale": 0.1, "unit": "kW"},
        "Phase-W Power Factor": {"start_address": 5036, "type": "INT16", "scale": 0.01},
        "Phase-W Load Capacity": {"start_address": 5037, "type": "UINT16", "unit": "%"},
        
        # Daily and Total Energy
        "Daily Charge": {"start_address": 5039, "length": 2, "type": "UINT16", "scale": 0.1, "unit": "kWh"},
        "Daily Discharge": {"start_address": 5041, "length": 2, "type": "UINT16", "scale": 0.1, "unit": "kWh"},
        "Daily Gains": {"start_address": 5043, "length": 2, "type": "INT32", "unit": "Yuan"},
        
        "Total Charge": {"start_address": 5045, "length": 2, "type": "UINT32", "scale": 0.1, "unit": "kWh"},
        "Total Discharge": {"start_address": 5047, "length": 2, "type": "UINT32", "scale": 0.1, "unit": "kWh"},
        "Total Gains": {"start_address": 5049, "length": 2, "type": "INT32", "unit": "Yuan"},
        
        "Current Electricity Price": {"start_address": 5051, "length": 2, "type": "UINT32", "scale": 0.0001, "unit": "Yuan"},
        
        # Status and Power Availability
        "On-Grid/Off-Grid Status": {"start_address": 5053, "type": "UINT16"},
        "Available Power": {"start_address": 5054, "type": "UINT16", "scale": 0.1, "unit": "kVA"},
        "Remote Control Status": {"start_address": 5055, "type": "UINT16"},
        
        # Battery and BMS System Status
        "BMS System Status": {"start_address": 5200, "type": "UINT16"},
        "Total Battery Voltage": {"start_address": 5202, "type": "UINT16", "scale": 0.1, "unit": "V"},
        "Total Battery Current": {"start_address": 5203, "type": "INT16", "scale": 0.1, "unit": "A"},
        "Battery Group SOC": {"start_address": 5204, "type": "UINT16", "scale": 0.1, "unit": "%"},
        "Battery Group SOH": {"start_address": 5205, "type": "UINT16", "scale": 0.1, "unit": "%"},
        "Charge Limit Current": {"start_address": 5206, "type": "UINT16", "scale": 0.1, "unit": "A"},
        "Discharge Limit Current": {"start_address": 5207, "type": "UINT16", "scale": 0.1, "unit": "A"},
        "Charge Limit Voltage": {"start_address": 5208, "type": "UINT16", "scale": 0.1, "unit": "V"},
    }

    def __init__(self, ip_address, port=502):
        self.client = ModbusTcpClient(ip_address, port=port)

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()

    def read_ascii(self, start_address, count):
        """Read ASCII data from consecutive registers and convert to string."""
        result = self.client.read_input_registers(start_address, count)
        if result.isError():
            print(f"Error reading ASCII registers from {start_address} to {start_address + count - 1}")
            return None
        # Convert register values to ASCII characters
        ascii_string = ''.join([chr((reg >> 8) & 0xFF) + chr(reg & 0xFF) for reg in result.registers])
        return ascii_string.strip('\x00')

    def read_uint16(self, start_address, count=1):
        """Read UINT16 data."""
        result = self.client.read_input_registers(start_address, count)
        if result.isError():
            print(f"Error reading UINT16 registers from {start_address} to {start_address + count - 1}")
            return None
        return result.registers

    def read_int16(self, start_address, count=1):
        """Read INT16 data and interpret it as signed."""
        result = self.client.read_input_registers(start_address, count)
        if result.isError():
            print(f"Error reading INT16 registers from {start_address} to {start_address + count - 1}")
            return None
        return [struct.unpack('>h', struct.pack('>H', reg))[0] for reg in result.registers]

    def read_uint32(self, start_address):
        """Read UINT32 data by combining two consecutive 16-bit registers."""
        result = self.client.read_input_registers(start_address, 2)
        if result.isError():
            print(f"Error reading UINT32 registers from {start_address} to {start_address + 1}")
            return None
        # Combine two 16-bit registers into a 32-bit unsigned integer
        high, low = result.registers
        return (high << 16) + low

    def read_int32(self, start_address):
        """Read INT32 data by combining two consecutive 16-bit registers and interpreting as signed."""
        result = self.client.read_input_registers(start_address, 2)
        if result.isError():
            print(f"Error reading INT32 registers from {start_address} to {start_address + 1}")
            return None
        # Combine two 16-bit registers into a 32-bit signed integer
        high, low = result.registers
        combined = (high << 16) + low
        return struct.unpack('>i', struct.pack('>I', combined))[0]

    def read_registers(self):
        return_data = {}
        """Read registers based on a register map."""
        for name, properties in self.register_map.items():
            start_address = properties['start_address']
            length = properties.get('length', 1)
            data_type = properties.get('type', 'UINT16')
            scale = properties.get('scale', 1)
            unit = properties.get('unit', '')

            # Read data based on type
            if data_type == 'ASCII':
                value = self.read_ascii(start_address, length)
            elif data_type == 'UINT16':
                raw_values = self.read_uint16(start_address, length)
                if raw_values is not None:
                    # Apply scale and round to 1 decimal place
                    value = [round(v * scale, 1) for v in raw_values]
                else:
                    value = None
            elif data_type == 'INT16':
                raw_values = self.read_int16(start_address, length)
                if raw_values is not None:
                    # Apply scale and round to 1 decimal place
                    value = [round(v * scale, 1) for v in raw_values]
                else:
                    value = None
            elif data_type == 'UINT32':
                raw_value = self.read_uint32(start_address)
                value = round(raw_value * scale, 1) if raw_value is not None else None
            elif data_type == 'INT32':
                raw_value = self.read_int32(start_address)
                value = round(raw_value * scale, 1) if raw_value is not None else None
            else:
                print(f"Unsupported data type: {data_type}")
                value = None

            # Output the result
            if value is not None:
                if isinstance(value, list) and len(value) == 1:
                    value = value[0]  # Unpack single-value lists
                print(f"{name}: {value} {unit}")
                return_data[name] = { 
                    'value': value,
                    'unit': unit
                }
        return return_data
    
    def read_version(self):
        return self.read_ascii(4810, 5)
    def read_model(self):
        return self.read_ascii(4800, 10)

# Example usage
if __name__ == "__main__":
    # Define the Modbus server details
    ip_address = "192.168.1.91"
    
    # Define the register map
    
    # Instantiate and use the ModbusReader
    reader = KehuaClient(ip_address)
    
    if reader.connect():
        reader.read_registers()
        reader.close()
    else:
        print("Failed to connect to the Modbus server.")