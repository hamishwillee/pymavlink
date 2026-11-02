#!/usr/bin/env python3
"""
Module to test MAVXML
"""

import unittest
try:
    from importlib.resources import files as importlib_files
except ImportError:
    # importlib.resources.files() requires Python 3.9+; use backport for older versions
    from importlib_resources import files as importlib_files

from pymavlink.generator.mavparse import MAVXML
from pymavlink.generator.mavparse import MAVParseError
from pymavlink.generator.mavparse import merge_enums

class MAVXMLTest(unittest.TestCase):
    """
    Class to test MAVXML
    """

    def test_fields_number(self):
        """Test that a message can have at most 64 fields"""
        test_filename = "64-fields.xml"
        test_filepath = importlib_files(__spec__.parent).joinpath(test_filename)
        xml = MAVXML(test_filepath)
        count = len(xml.message[0].fields)
        self.assertEqual(count, 64)

        test_filename = "65-fields.xml"
        test_filepath = importlib_files(__spec__.parent).joinpath(test_filename)
        with self.assertRaises(MAVParseError):
            _ = MAVXML(test_filepath)


    def test_wire_protocol_version(self):
        """Test that an unknown MAVLink wire protocol version raises an exception"""
        with self.assertRaises(MAVParseError):
            _ = MAVXML(filename="", wire_protocol_version=42)


    def test_wip_deprecated_superseded(self):
        """Test that wip/deprecated/superseded are parsed for messages, enums and enum entries"""
        test_filename = "wip_deprecated_superseded.xml"
        test_filepath = importlib_files(__spec__.parent).joinpath(test_filename)
        xml = MAVXML(test_filepath)

        messages = {m.name: m for m in xml.message}
        self.assertTrue(messages["WIP_MESSAGE"].wip)
        self.assertIsNone(messages["WIP_MESSAGE"].deprecated)
        self.assertIsNone(messages["WIP_MESSAGE"].superseded)

        self.assertFalse(messages["DEPRECATED_MESSAGE"].wip)
        self.assertIsNotNone(messages["DEPRECATED_MESSAGE"].deprecated)
        self.assertEqual(messages["DEPRECATED_MESSAGE"].deprecated.since, "2024-01")
        self.assertEqual(messages["DEPRECATED_MESSAGE"].deprecated.replaced_by, "WIP_MESSAGE")

        self.assertFalse(messages["SUPERSEDED_MESSAGE"].wip)
        self.assertIsNotNone(messages["SUPERSEDED_MESSAGE"].superseded)
        self.assertEqual(messages["SUPERSEDED_MESSAGE"].superseded.since, "2024-01")
        self.assertEqual(messages["SUPERSEDED_MESSAGE"].superseded.replaced_by, "WIP_MESSAGE")

        enums = {e.name: e for e in xml.enum}
        self.assertTrue(enums["WIP_ENUM"].wip)
        self.assertIsNone(enums["WIP_ENUM"].deprecated)
        self.assertIsNone(enums["WIP_ENUM"].superseded)
        self.assertFalse(enums["DEPRECATED_ENUM"].wip)
        self.assertFalse(enums["SUPERSEDED_ENUM"].wip)
        self.assertFalse(enums["ENTRY_FLAGS_ENUM"].wip)
        self.assertIsNone(enums["ENTRY_FLAGS_ENUM"].deprecated)
        self.assertIsNone(enums["ENTRY_FLAGS_ENUM"].superseded)
        # an enum-level flag is not copied onto the parsed entries; the
        # generators apply it to unflagged entries themselves
        self.assertFalse(enums["WIP_ENUM"].entry[0].wip)

        self.assertIsNotNone(enums["DEPRECATED_ENUM"].deprecated)
        self.assertEqual(enums["DEPRECATED_ENUM"].deprecated.replaced_by, "SOME_OTHER_ENUM")
        self.assertIsNotNone(enums["SUPERSEDED_ENUM"].superseded)
        self.assertEqual(enums["SUPERSEDED_ENUM"].superseded.replaced_by, "SOME_OTHER_ENUM")

        entries = {e.name: e for e in enums["ENTRY_FLAGS_ENUM"].entry}
        self.assertTrue(entries["ENTRY_FLAGS_ENUM_WIP"].wip)
        self.assertIsNone(entries["ENTRY_FLAGS_ENUM_WIP"].deprecated)
        self.assertIsNone(entries["ENTRY_FLAGS_ENUM_WIP"].superseded)

        self.assertIsNotNone(entries["ENTRY_FLAGS_ENUM_DEPRECATED"].deprecated)
        self.assertEqual(entries["ENTRY_FLAGS_ENUM_DEPRECATED"].deprecated.replaced_by, "ENTRY_FLAGS_ENUM_WIP")

        self.assertIsNotNone(entries["ENTRY_FLAGS_ENUM_SUPERSEDED"].superseded)
        self.assertEqual(entries["ENTRY_FLAGS_ENUM_SUPERSEDED"].superseded.replaced_by, "ENTRY_FLAGS_ENUM_WIP")

        self.assertFalse(entries["ENTRY_FLAGS_ENUM_PLAIN"].wip)
        self.assertIsNone(entries["ENTRY_FLAGS_ENUM_PLAIN"].deprecated)
        self.assertIsNone(entries["ENTRY_FLAGS_ENUM_PLAIN"].superseded)

        # entries record the flags of the enum declaration they came from
        self.assertTrue(enums["WIP_ENUM"].entry[0].enum_wip)
        self.assertIsNotNone(enums["DEPRECATED_ENUM"].entry[0].enum_deprecated)
        self.assertIsNotNone(enums["SUPERSEDED_ENUM"].entry[0].enum_superseded)
        self.assertFalse(entries["ENTRY_FLAGS_ENUM_WIP"].enum_wip)
        self.assertIsNone(entries["ENTRY_FLAGS_ENUM_DEPRECATED"].enum_deprecated)
        self.assertIsNone(entries["ENTRY_FLAGS_ENUM_SUPERSEDED"].enum_superseded)


    def test_extended_enum_flags(self):
        """Test that merging an extended enum keeps each declaration's flags with its own entries"""
        dialect = MAVXML(importlib_files(__spec__.parent).joinpath("wip_deprecated_superseded.xml"))
        base = MAVXML(importlib_files(__spec__.parent).joinpath("wip_deprecated_superseded_base.xml"))
        # mavgen lists the including file before the files it includes
        merge_enums([dialect, base])

        enums = {e.name: e for e in dialect.enum}
        self.assertNotIn("EXTENDED_DEPRECATED_ENUM", [e.name for e in base.enum])
        self.assertNotIn("EXTENDED_WIP_ENUM", [e.name for e in base.enum])

        # flagged in the included file only: the merged enum and the
        # included file's entry are flagged, the extension's entry is not
        merged = enums["EXTENDED_DEPRECATED_ENUM"]
        self.assertIsNotNone(merged.deprecated)
        self.assertEqual(merged.deprecated.replaced_by, "SOME_OTHER_ENUM")
        entries = {e.name: e for e in merged.entry}
        self.assertIsNotNone(entries["EXTENDED_DEPRECATED_ENUM_FROM_FLAGGED_BASE"].enum_deprecated)
        self.assertIsNone(entries["EXTENDED_DEPRECATED_ENUM_FROM_UNFLAGGED_DIALECT"].enum_deprecated)
        self.assertIsNone(entries["EXTENDED_DEPRECATED_ENUM_ENUM_END"].enum_deprecated)

        # flagged in the including file only: the merged enum and the
        # including file's entry are flagged, the included file's entry is not
        merged = enums["EXTENDED_WIP_ENUM"]
        self.assertTrue(merged.wip)
        entries = {e.name: e for e in merged.entry}
        self.assertFalse(entries["EXTENDED_WIP_ENUM_FROM_UNFLAGGED_BASE"].enum_wip)
        self.assertTrue(entries["EXTENDED_WIP_ENUM_FROM_FLAGGED_DIALECT"].enum_wip)
        self.assertFalse(entries["EXTENDED_WIP_ENUM_ENUM_END"].enum_wip)


if __name__ == '__main__':
    unittest.main()
