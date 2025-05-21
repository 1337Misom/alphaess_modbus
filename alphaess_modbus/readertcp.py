from pymodbus.client import AsyncModbusTcpClient
import json
from .reader import Reader
from pathlib import Path


class ReaderTCP(Reader):
    instrument: AsyncModbusTcpClient
    slave_id: int

    def __init__(
        self,
        ip=None,
        port=502,
        slave_id=int(0x55),
        debug=False,
        json_file=None,
        formatter=None,
    ) -> None:
        self.instrument = AsyncModbusTcpClient(ip, port=port)
        self.debug = debug
        self.slave_id = slave_id

        if formatter is not None:
            self.custom_formatter = formatter

        # Load register JSON
        if json_file is None:
            p = Path(__file__)
            json_file = p.absolute().with_name("registers.json")

        try:
            f = open(json_file)
            self.mapping = json.load(f)
        except OSError:
            raise RuntimeError(f"Could not find JSON file {json_file!r}")

    async def get_value(self, name) -> int:
        """Ask inverter for a specific register"""
        name = self.conform_name(name)
        register = await self.get_definition(name)
        if self.debug:
            print(f"{name} -> {register['hex']}")

        if self.instrument.connected is False:
            await self.instrument.connect()

        if register["type"] == "long":
            val = await self.instrument.read_holding_registers(
                int(register["address"]), count=2, slave=self.slave_id
            )

            if register["signed"] is True:
                val = self.instrument.convert_from_registers(
                    val.registers,
                    data_type=self.instrument.DATATYPE.INT32,
                    word_order="big",
                )
            else:
                val = self.instrument.convert_from_registers(
                    val.registers,
                    data_type=self.instrument.DATATYPE.UINT32,
                    word_order="big",
                )
        else:
            val = await self.instrument.read_holding_registers(
                int(register["address"]), count=1, slave=self.slave_id
            )

            if register["signed"] is True:
                val = self.instrument.convert_from_registers(
                    val.registers,
                    data_type=self.instrument.DATATYPE.INT16,
                    word_order="big",
                )
            else:
                val = self.instrument.convert_from_registers(
                    val.registers,
                    data_type=self.instrument.DATATYPE.UINT16,
                    word_order="big",
                )

        if register["decimals"] > 0:
            divisor = 10 ** register["decimals"]
            val = val / float(divisor)

        return val
