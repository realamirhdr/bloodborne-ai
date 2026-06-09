from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass
class Record:
    name: str
    type: str
    text: str
    metadata: dict = field(default_factory=dict)


def load_all(data_dir: str | Path = "data/raw") -> list[Record]:
    data_dir = Path(data_dir)
    records: list[Record] = []
    for path in sorted(data_dir.glob("*.xml")):
        records.extend(_load_file(path))
    return records


def _load_file(path: Path) -> list[Record]:
    try:
        root = _parse_xml(path)
    except ET.ParseError as exc:
        print(f"[warn] skipping {path.name}: {exc}")
        return []

    stem = path.stem
    src = path.name

    if stem == "bossInfo":
        return _parse_wrapped(root, "boss", "boss", src)
    if stem == "npcInfo":
        return _parse_wrapped(root, "npc", "npc", src)
    if stem == "attireInfoUpdate":
        return _parse_attire(root, src)
    if stem == "mainXML":
        return _parse_runes(root, src)
    if stem in ("weapons", "firearmWeapons"):
        type_ = "weapon" if stem == "weapons" else "firearm"
        return _parse_flat(root, type_, src)
    return []


def _parse_xml(path: Path) -> ET.Element:
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return ET.fromstring(raw.decode("utf-16"))
    return ET.parse(path).getroot()


def _txt(el: ET.Element | None) -> str:
    if el is None or not el.text:
        return ""
    return " ".join(el.text.split())


def _all_text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return " ".join(t.strip() for t in el.itertext() if t.strip())


def _join(*parts: str) -> str:
    return "\n\n".join(p for p in parts if p)


def _clean_name(raw: str) -> str:
    for sep in (" is a ", " is an ", " (", ","):
        if sep in raw:
            return raw.split(sep)[0].strip()
    return raw.strip()


def _loc_text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    place = el.get("place", "")
    if place.upper() == "NULL":
        place = ""
    body = " ".join((el.text or "").split())
    return f"{place}: {body}" if place else body


def _parse_wrapped(root: ET.Element, tag: str, type_: str, src: str) -> list[Record]:
    records = []
    for el in root.iter(tag):
        raw_name = _txt(el.find("name"))
        if not raw_name:
            continue
        name = _clean_name(raw_name)
        dialogue = "\n".join(
            _txt(line) for line in el.findall(".//line") if _txt(line)
        )
        text = _join(
            _txt(el.find("description")),
            _txt(el.find("notes")),
            _loc_text(el.find("location")),
            dialogue,
        )
        records.append(Record(name=name, type=type_, text=text, metadata={"source_file": src, "name": name, "type": type_}))
    return records


def _parse_attire(root: ET.Element, src: str) -> list[Record]:
    records = []
    for el in root.iter("attire"):
        name_el = el.find("attireName")
        if name_el is None:
            continue
        attire_list = name_el.get("attireList", "")
        name = attire_list.replace("_", " ") if attire_list else _clean_name(_txt(name_el))
        if not name:
            continue
        text = _join(
            _txt(el.find("description")),
            _txt(el.find("trivia")),
            _loc_text(el.find("location")),
        )
        records.append(Record(name=name, type="attire", text=text, metadata={"source_file": src, "name": name, "type": "attire"}))
    return records


def _parse_runes(root: ET.Element, src: str) -> list[Record]:
    records = []
    for el in root.iter("caryllRune"):
        name_el = el.find("runeName")
        if name_el is None:
            continue
        rune_list = name_el.get("runeList", "")
        name = rune_list.replace("_", " ") if rune_list else _txt(name_el)
        if not name:
            continue
        text = _join(
            _txt(el.find("description")),
            _all_text(el.find("locationArea")),
            _txt(el.find("effect")),
            _txt(el.find("notes")),
        )
        records.append(Record(name=name, type="rune", text=text, metadata={"source_file": src, "name": name, "type": "rune"}))
    return records


def _parse_flat(root: ET.Element, type_: str, src: str) -> list[Record]:
    records: list[Record] = []
    current: dict[str, str] = {}

    def flush() -> None:
        if not current.get("name"):
            return
        name = _clean_name(current["name"])
        text = _join(
            current.get("description", ""),
            current.get("notes", ""),
            current.get("trivia", ""),
            current.get("location", ""),
        )
        records.append(Record(name=name, type=type_, text=text, metadata={"source_file": src, "name": name, "type": type_}))

    for child in root:
        tag = child.tag.lower()
        val = (child.text or "").strip()
        if tag == "name":
            flush()
            current = {"name": val}
        elif tag in ("description", "notes", "trivia"):
            current[tag] = val
        elif tag == "location":
            place = child.get("place", "")
            current["location"] = f"{place}: {val}" if place else val

    flush()
    return records


if __name__ == "__main__":
    import sys

    data_dir = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).parent.parent.parent / "data" / "raw"
    )
    records = load_all(data_dir)
    print(f"Loaded {len(records)} records\n{'=' * 60}")
    for r in records[:3]:
        print(f"[{r.type.upper()}] {r.name}")
        print(f"Metadata: {r.metadata}")
        print(r.text[:400])
        print("-" * 60)
