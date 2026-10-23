#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

from bsdconv import Bsdconv


def mappings(text, table_format="xp"):
    if table_format == "xp":
        # XP rows are comma-separated; a blank CNS column has no mapping.
        row = re.compile(r"^\s*[0-9A-Fa-f]{4},([0-9A-Fa-f]{4}),[^,]*,\s*(?:([0-9]{1,2})-([0-9A-Fa-f]{4}))?\s*,")
        candidate = re.compile(r"^\s*[0-9A-Fa-f]{4},[0-9A-Fa-f]{4},")
    else:
        # Locate each record; targets come only from its source columns.
        row = re.compile(r"^\s*[0-9A-Fa-f]{4}\s+([0-9A-Fa-f]{4})\s+([0-9]{1,2})-([0-9A-Fa-f]{4})(?:\s|$)")
        candidate = re.compile(r"^\s*[0-9A-Fa-f]{4}\s+[0-9A-Fa-f]{4}\b")
    source_fields = re.compile(r"\b([0-9]{1,2})-([0-9A-Fa-f]{4})(?:\s+([0-9A-Fa-f]{4,6}))?\s*$")
    converter = None
    if table_format == "xp":
        converter = Bsdconv("bsdconv:unicode:bsdconv")
        if not converter:
            raise ValueError(Bsdconv.error())

    result = {}
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        match = row.match(line)
        if not match:
            if candidate.match(line):
                raise ValueError(f"Line {number}: invalid CNS mapping: {line.strip()}")
            continue
        pua, plane, code = match.groups()
        if plane is None:
            continue
        pua, plane, code = int(pua, 16), int(plane, 10), int(code, 16)
        if not (0xE000 <= pua <= 0xF8FF and 1 <= plane <= 16
                and 0x21 <= code >> 8 <= 0x7E and 0x21 <= code & 0xFF <= 0x7E):
            raise ValueError(f"Line {number}: invalid PUA or CNS code: {line.strip()}")

        # CNS planes are decimal in the PDF, hexadecimal in bsdconv data.
        source = f"01{pua:04X}"
        target = f"02{plane:02X}{code:04X}"
        if table_format == "unicode":
            # Long phonetic fields can move the source columns onto the next line.
            end = number
            record = line[match.end():]
            while end < len(lines) and lines[end].strip() and not candidate.match(lines[end]):
                record += " " + lines[end].strip()
                end += 1
            source_match = source_fields.search(record)
            if not source_match:
                continue
            source_plane, source_code, unicode_value = source_match.groups()
            source_plane, source_code = int(source_plane, 10), int(source_code, 16)
            # Source CNS includes extended planes beyond the original 16.
            if not (1 <= source_plane <= 0xFF
                    and 0x21 <= source_code >> 8 <= 0x7E
                    and 0x21 <= source_code & 0xFF <= 0x7E):
                raise ValueError(f"Line {number}: invalid source CNS code: {record.strip()}")
            target = f"02{source_plane:02X}{source_code:04X}"
            if unicode_value:
                cp = int(unicode_value, 16)
                if (0 <= cp <= 0x10FFFF and not 0xD800 <= cp <= 0xDFFF
                        and not 0xE000 <= cp <= 0xF8FF
                        and not 0xF0000 <= cp <= 0xFFFFF
                        and not 0x100000 <= cp <= 0x10FFFF
                        and not 0xFDD0 <= cp <= 0xFDEF
                        and cp & 0xFFFF not in (0xFFFE, 0xFFFF)):
                    value = f"{cp:X}"
                    target = "01" + value.zfill(len(value) + len(value) % 2)
        else:
            target = converter.uconv(target)
            counters = converter.counter()
            if not target or counters.get("IERR", 0) or counters.get("OERR", 0):
                raise ValueError(f"Line {number}: failed to convert CNS code")
        if source in result and result[source] != target:
            raise ValueError(f"Line {number}: conflicting mapping for {source}")
        result[source] = target

    if not result:
        raise ValueError(f"No mappings found; expected pdftotext -layout output for {table_format}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Generate mappings from judicial PUA PDF text")
    parser.add_argument("--format", choices=("xp", "unicode"), default="xp",
                        help="source package format (default: xp)")
    parser.add_argument("table", type=Path, help="text extracted with pdftotext -layout")
    args = parser.parse_args()
    try:
        result = mappings(args.table.read_text(encoding="utf-8"), args.format)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    for source, target in sorted(result.items()):
        print(f"{source}\t{target}")
    unresolved = sum(target.startswith("02") for target in result.values())
    print(f"Generated {len(result)} mappings; {unresolved} retained as CNS codes", file=sys.stderr)


if __name__ == "__main__":
    main()
