"""
Comprehensive tests for J1939 NAME decoding based on SAE J1939/81 analysis.

Tests cover:
- Case Study 1: Allison Transmission (wire data: 6400400000030310)
- Case Study 2: Caterpillar C15 Engine (wire data: D06B010100000080)
- from_wire_data byte-swap correctness
- Individual field extraction at boundary values
- Industry group, function, and manufacturer name lookups
- Edge cases (all zeros, all ones, max values per field)
"""
import pytest
from truckdevil.libs.j1939_name import J1939Name


# ---------------------------------------------------------------------------
# Case Study 1: Allison Transmission
# Raw CAN Data (Hex): 18EEFF03  64 00 40 00 00 03 03 10
# Wire bytes (LSB first): 64 00 40 00 00 03 03 10
# 64-bit NAME (MSB first): 0x1003030000400064
# ---------------------------------------------------------------------------


class TestAllisonTransmission:
    """Decode Allison Transmission Address Claimed response."""

    @pytest.fixture()
    def name(self):
        return J1939Name.from_wire_data("6400400000030310")

    def test_identity_number(self, name):
        assert name.identity_number == 100

    def test_manufacturer_code(self, name):
        assert name.manufacturer_code == 2

    def test_ecu_instance(self, name):
        assert name.ecu_instance == 0

    def test_function_instance(self, name):
        assert name.function_instance == 0

    def test_function(self, name):
        assert name.function == 3

    def test_vehicle_system(self, name):
        assert name.vehicle_system == 1

    def test_vehicle_system_instance(self, name):
        assert name.vehicle_system_instance == 0

    def test_industry_group(self, name):
        assert name.industry_group == 1

    def test_arbitrary_address_capable(self, name):
        assert name.arbitrary_address_capable == 0

    def test_manufacturer_name(self, name):
        assert name.get_manufacturer_name() == "Allison Transmission, Inc."

    def test_function_name(self, name):
        assert name.get_function_name() == "Transmission"

    def test_industry_group_name(self, name):
        assert name.get_industry_group_name() == "On-highway equipment"

    def test_str_contains_key_info(self, name):
        s = str(name)
        assert "Allison" in s
        assert "Transmission" in s
        assert "Arbitrary Address Capable: No" in s


# ---------------------------------------------------------------------------
# Case Study 2: Caterpillar C15 Engine
# Raw CAN Data (Hex): 18EEFF00  D0 6B 01 01 00 00 00 80
# Wire bytes (LSB first): D0 6B 01 01 00 00 00 80
# 64-bit NAME (MSB first): 0x8000000001016BD0
# ---------------------------------------------------------------------------


class TestCaterpillarC15:
    """Decode Caterpillar C15 Engine Address Claimed response."""

    @pytest.fixture()
    def name(self):
        return J1939Name.from_wire_data("D06B010100000080")

    def test_identity_number(self, name):
        assert name.identity_number == 93136

    def test_manufacturer_code(self, name):
        assert name.manufacturer_code == 8

    def test_ecu_instance(self, name):
        assert name.ecu_instance == 0

    def test_function_instance(self, name):
        assert name.function_instance == 0

    def test_function(self, name):
        assert name.function == 0

    def test_vehicle_system(self, name):
        assert name.vehicle_system == 0

    def test_vehicle_system_instance(self, name):
        assert name.vehicle_system_instance == 0

    def test_industry_group(self, name):
        assert name.industry_group == 0

    def test_arbitrary_address_capable(self, name):
        assert name.arbitrary_address_capable == 1

    def test_manufacturer_name(self, name):
        assert name.get_manufacturer_name() == "Caterpillar Inc."

    def test_function_name(self, name):
        assert name.get_function_name() == "Engine"

    def test_industry_group_name(self, name):
        assert name.get_industry_group_name() == "global, applies to all"

    def test_str_contains_key_info(self, name):
        s = str(name)
        assert "Caterpillar" in s
        assert "Engine" in s
        assert "Arbitrary Address Capable: Yes" in s


# ---------------------------------------------------------------------------
# from_wire_data byte-swap correctness
# ---------------------------------------------------------------------------


class TestFromWireData:
    """Verify from_wire_data correctly reverses byte order."""

    def test_round_trip_allison(self):
        """Wire data → NAME int → back to wire bytes matches original."""
        wire = "6400400000030310"
        name = J1939Name.from_wire_data(wire)
        # Reconstruct wire bytes from name_int (little-endian)
        reconstructed = name.name_int.to_bytes(8, byteorder="little").hex()
        assert reconstructed == wire.lower()

    def test_round_trip_caterpillar(self):
        wire = "D06B010100000080"
        name = J1939Name.from_wire_data(wire)
        reconstructed = name.name_int.to_bytes(8, byteorder="little").hex()
        assert reconstructed == wire.lower()

    def test_from_wire_data_same_as_int_constructor(self):
        """from_wire_data should produce the same result as passing the swapped integer."""
        name_wire = J1939Name.from_wire_data("6400400000030310")
        name_int = J1939Name(0x1003030000400064)
        assert name_wire.name_int == name_int.name_int
        assert name_wire.identity_number == name_int.identity_number
        assert name_wire.manufacturer_code == name_int.manufacturer_code
        assert name_wire.function == name_int.function
        assert name_wire.industry_group == name_int.industry_group

    def test_from_wire_data_with_0x_prefix(self):
        """from_wire_data should strip 0x prefix if present."""
        name = J1939Name.from_wire_data("0xD06B010100000080")
        assert name.arbitrary_address_capable == 1
        assert name.manufacturer_code == 8

    def test_all_zeros(self):
        """All-zero wire data should decode to all-zero fields."""
        name = J1939Name.from_wire_data("0000000000000000")
        assert name.identity_number == 0
        assert name.manufacturer_code == 0
        assert name.ecu_instance == 0
        assert name.function_instance == 0
        assert name.function == 0
        assert name.reserved == 0
        assert name.vehicle_system == 0
        assert name.vehicle_system_instance == 0
        assert name.industry_group == 0
        assert name.arbitrary_address_capable == 0

    def test_all_ff(self):
        """All-0xFF wire data: every field at maximum."""
        name = J1939Name.from_wire_data("FFFFFFFFFFFFFFFF")
        assert name.identity_number == 0x1FFFFF       # 21 bits max
        assert name.manufacturer_code == 0x7FF         # 11 bits max
        assert name.ecu_instance == 0x07               # 3 bits max
        assert name.function_instance == 0x1F          # 5 bits max
        assert name.function == 0xFF                   # 8 bits max
        assert name.reserved == 1                      # 1 bit max
        assert name.vehicle_system == 0x7F             # 7 bits max
        assert name.vehicle_system_instance == 0x0F    # 4 bits max
        assert name.industry_group == 0x07             # 3 bits max
        assert name.arbitrary_address_capable == 1     # 1 bit max


# ---------------------------------------------------------------------------
# Individual field extraction — set one field at a time
# ---------------------------------------------------------------------------


class TestFieldExtraction:
    """Verify that each field is extracted from the correct bit positions."""

    def test_identity_number_only(self):
        """Identity Number occupies bits 0-20 (21 bits)."""
        # Set bits 0-20 to all 1s: 0x1FFFFF
        name = J1939Name(0x1FFFFF)
        assert name.identity_number == 0x1FFFFF
        assert name.manufacturer_code == 0
        assert name.function == 0

    def test_manufacturer_code_only(self):
        """Manufacturer Code occupies bits 21-31 (11 bits)."""
        # Set bits 21-31 to all 1s: 0x7FF << 21 = 0xFFE00000
        name = J1939Name(0x7FF << 21)
        assert name.identity_number == 0
        assert name.manufacturer_code == 0x7FF
        assert name.ecu_instance == 0

    def test_ecu_instance_only(self):
        """ECU Instance occupies bits 32-34 (3 bits)."""
        name = J1939Name(0x07 << 32)
        assert name.ecu_instance == 7
        assert name.function_instance == 0

    def test_function_instance_only(self):
        """Function Instance occupies bits 35-39 (5 bits)."""
        name = J1939Name(0x1F << 35)
        assert name.function_instance == 31
        assert name.ecu_instance == 0
        assert name.function == 0

    def test_function_only(self):
        """Function occupies bits 40-47 (8 bits)."""
        name = J1939Name(0xFF << 40)
        assert name.function == 255
        assert name.function_instance == 0
        assert name.reserved == 0

    def test_reserved_bit_only(self):
        """Reserved bit is bit 48."""
        name = J1939Name(1 << 48)
        assert name.reserved == 1
        assert name.function == 0
        assert name.vehicle_system == 0

    def test_vehicle_system_only(self):
        """Vehicle System occupies bits 49-55 (7 bits)."""
        name = J1939Name(0x7F << 49)
        assert name.vehicle_system == 127
        assert name.reserved == 0
        assert name.vehicle_system_instance == 0

    def test_vehicle_system_instance_only(self):
        """Vehicle System Instance occupies bits 56-59 (4 bits)."""
        name = J1939Name(0x0F << 56)
        assert name.vehicle_system_instance == 15
        assert name.vehicle_system == 0
        assert name.industry_group == 0

    def test_industry_group_only(self):
        """Industry Group occupies bits 60-62 (3 bits)."""
        name = J1939Name(0x07 << 60)
        assert name.industry_group == 7
        assert name.vehicle_system_instance == 0
        assert name.arbitrary_address_capable == 0

    def test_aac_bit_only(self):
        """Arbitrary Address Capable is bit 63."""
        name = J1939Name(1 << 63)
        assert name.arbitrary_address_capable == 1
        assert name.industry_group == 0


# ---------------------------------------------------------------------------
# Industry Group name lookups (SPN 2846)
# ---------------------------------------------------------------------------


class TestIndustryGroupNames:
    """Validate industry group name lookups against the J1939 standard."""

    @pytest.mark.parametrize("ig_value,expected_name", [
        (0, "global, applies to all"),
        (1, "On-highway equipment"),
        (2, "agricultural and forestry equipment"),
        (3, "construction equipment"),
        (4, "marine"),
        (5, "industrial-process control-stationary (gen-sets)"),
    ])
    def test_industry_group_name(self, ig_value, expected_name):
        name = J1939Name(ig_value << 60)
        assert name.get_industry_group_name() == expected_name


# ---------------------------------------------------------------------------
# Function name lookups (SPN 2841)
# ---------------------------------------------------------------------------


class TestFunctionNames:
    """Validate common function code name lookups."""

    @pytest.mark.parametrize("func_code,expected_name", [
        (0, "Engine"),
        (3, "Transmission"),
        (9, "Brakes - System Controller"),
    ])
    def test_function_name(self, func_code, expected_name):
        name = J1939Name(func_code << 40)
        assert name.get_function_name() == expected_name


# ---------------------------------------------------------------------------
# Manufacturer name lookups (SPN 2838)
# ---------------------------------------------------------------------------


class TestManufacturerNames:
    """Validate manufacturer code name lookups."""

    @pytest.mark.parametrize("mfg_code,expected_name", [
        (2, "Allison Transmission, Inc."),
        (8, "Caterpillar Inc."),
    ])
    def test_manufacturer_name(self, mfg_code, expected_name):
        name = J1939Name(mfg_code << 21)
        assert name.get_manufacturer_name() == expected_name


# ---------------------------------------------------------------------------
# Byte-to-bit mapping verification (per J1939-81 spec)
# ---------------------------------------------------------------------------


class TestByteMapping:
    """
    Verify the byte-to-bit mapping described in the J1939-81 specification.

    Wire byte layout (little-endian):
        Byte 1 (LSB): Identity Number bits 0-7
        Byte 2:       Identity Number bits 8-15
        Byte 3:       Identity Number bits 16-20 (low 5 bits) +
                       Manufacturer Code bits 0-2 (high 3 bits)
        Byte 4:       Manufacturer Code bits 3-10
        Byte 5:       ECU Instance (low 3 bits) +
                       Function Instance (high 5 bits)
        Byte 6:       Function (8 bits)
        Byte 7:       Reserved (bit 0) + Vehicle System (bits 1-7)
        Byte 8 (MSB): Vehicle System Instance (bits 0-3) +
                       Industry Group (bits 4-6) +
                       Arbitrary Address Capable (bit 7)
    """

    def test_byte1_identity_number_lsb(self):
        """Byte 1 carries Identity Number bits 0-7."""
        # Set byte 1 to 0xFF, rest zero
        name = J1939Name.from_wire_data("FF00000000000000")
        assert name.identity_number == 0xFF

    def test_byte2_identity_number_mid(self):
        """Byte 2 carries Identity Number bits 8-15."""
        name = J1939Name.from_wire_data("00FF000000000000")
        assert name.identity_number == 0xFF00

    def test_byte3_split(self):
        """Byte 3 low 5 bits are Identity Number MSBs; high 3 bits are Manufacturer Code LSBs."""
        # Byte 3 = 0xFF: bits 0-4 -> Identity Number bits 16-20, bits 5-7 -> Mfg Code bits 0-2
        name = J1939Name.from_wire_data("0000FF0000000000")
        assert name.identity_number == 0x1F0000  # 5 bits = 0x1F shifted left 16
        assert name.manufacturer_code == 0x07     # 3 bits from byte 3

    def test_byte4_manufacturer_msb(self):
        """Byte 4 carries Manufacturer Code bits 3-10."""
        name = J1939Name.from_wire_data("000000FF00000000")
        assert name.manufacturer_code == 0x7F8  # bits 3-10 from byte 4

    def test_byte5_split(self):
        """Byte 5 low 3 bits are ECU Instance; high 5 bits are Function Instance."""
        name = J1939Name.from_wire_data("00000000FF000000")
        assert name.ecu_instance == 0x07   # 3 bits max
        assert name.function_instance == 0x1F  # 5 bits max

    def test_byte6_function(self):
        """Byte 6 carries the full 8-bit Function code."""
        name = J1939Name.from_wire_data("0000000000FF0000")
        assert name.function == 0xFF

    def test_byte7_split(self):
        """Byte 7 bit 0 is Reserved; bits 1-7 are Vehicle System."""
        # Byte 7 = 0xFF
        name = J1939Name.from_wire_data("000000000000FF00")
        assert name.reserved == 1
        assert name.vehicle_system == 0x7F  # 7 bits max

    def test_byte8_split(self):
        """Byte 8 bits 0-3 are VS Instance; bits 4-6 are IG; bit 7 is AAC."""
        # Byte 8 = 0xFF
        name = J1939Name.from_wire_data("00000000000000FF")
        assert name.vehicle_system_instance == 0x0F  # 4 bits
        assert name.industry_group == 0x07            # 3 bits
        assert name.arbitrary_address_capable == 1    # 1 bit

    def test_byte8_industry_group_isolation(self):
        """Industry Group in byte 8 bits 4-6: value 0x10 = IG 1, AAC 0."""
        # 0x10 = 0b00010000 -> IG bits 4-6 = 001 = 1, AAC bit 7 = 0
        name = J1939Name.from_wire_data("0000000000000010")
        assert name.industry_group == 1
        assert name.arbitrary_address_capable == 0
        assert name.vehicle_system_instance == 0

    def test_byte8_aac_isolation(self):
        """AAC in byte 8 bit 7: value 0x80 = AAC 1, IG 0."""
        # 0x80 = 0b10000000 -> AAC = 1, IG = 0
        name = J1939Name.from_wire_data("0000000000000080")
        assert name.arbitrary_address_capable == 1
        assert name.industry_group == 0
        assert name.vehicle_system_instance == 0
