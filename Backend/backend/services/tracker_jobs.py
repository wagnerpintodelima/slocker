import json
from datetime import datetime
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from backend.models import Talhao, TalhaoChild


TALHAO_STATUS_PENDING = 0
TALHAO_STATUS_PROCESSED = 1
TALHAO_STATUS_ERROR = 2
TALHAO_STATUS_PROCESSING = 3


def process_tracker_file(talhao_id, file_path):
    file_content = Path(file_path).read_text(encoding="utf-8-sig")
    lines = [line.strip() for line in file_content.splitlines() if line.strip()]

    if not lines:
        raise ValueError("O arquivo esta vazio.")

    with transaction.atomic():
        talhao = Talhao.objects.select_for_update().get(pk=talhao_id)
        talhao.status = TALHAO_STATUS_PROCESSING
        talhao.save(update_fields=["status"])

        TalhaoChild.objects.filter(talhao=talhao).delete()

        total_saved = 0
        current_nmea_date = None
        now = timezone.now()
        items = []

        for line in lines:
            parsed = parse_tracker_line(line, current_nmea_date)
            if not parsed:
                continue

            if parsed.get("date_str"):
                current_nmea_date = parsed.get("date_str")

            items.append(
                TalhaoChild(
                    talhao=talhao,
                    sentence_type=parsed["sentence_type"],
                    raw_line=line,
                    latitude=parsed.get("latitude"),
                    longitude=parsed.get("longitude"),
                    speed=parsed.get("speed"),
                    satellites=parsed.get("satellites"),
                    happened_at=parsed.get("happened_at"),
                    created_at=now,
                    status=1,
                )
            )

        if items:
            TalhaoChild.objects.bulk_create(items, batch_size=1000)
            total_saved = len(items)

        if total_saved == 0:
            raise ValueError("Nenhuma linha valida de tracker foi encontrada no arquivo.")

        talhao.status = TALHAO_STATUS_PROCESSED
        talhao.save(update_fields=["status"])

    return total_saved


def get_or_create_talhao_by_tracker_path(file_path):
    talhao_name = Path(file_path).name
    talhao = Talhao.objects.filter(name=talhao_name).order_by("-created_at", "-id").first()

    if talhao:
        return talhao, False

    talhao = Talhao(
        name=talhao_name,
        created_at=timezone.now(),
        status=TALHAO_STATUS_PENDING,
    )
    talhao.save()
    return talhao, True


def append_tracker_package(file_path, lines, clear_existing=False):
    normalized_lines = []
    for line in (lines or []):
        if isinstance(line, dict):
            normalized_line = json.dumps(line, ensure_ascii=False)
        else:
            normalized_line = str(line).strip()

        if normalized_line:
            normalized_lines.append(normalized_line)

    if not normalized_lines:
        return None, 0

    with transaction.atomic():
        talhao, created = get_or_create_talhao_by_tracker_path(file_path)
        talhao = Talhao.objects.select_for_update().get(pk=talhao.pk)
        previous_count = TalhaoChild.objects.filter(talhao=talhao).count()
        talhao.status = TALHAO_STATUS_PROCESSING
        talhao.save(update_fields=["status"])

        if clear_existing:
            TalhaoChild.objects.filter(talhao=talhao).delete()
            previous_count = 0

        total_saved = append_tracker_lines_to_talhao(talhao, normalized_lines)
        current_count = previous_count + total_saved

        if total_saved > 0:
            talhao.status = TALHAO_STATUS_PROCESSED
            talhao.save(update_fields=["status"])

    return talhao, total_saved, created, previous_count, current_count


def mark_talhao_error(talhao_id):
    Talhao.objects.filter(pk=talhao_id).update(status=TALHAO_STATUS_ERROR)


def append_tracker_lines_to_talhao(talhao, lines):
    total_saved = 0
    current_nmea_date = get_last_nmea_date_for_talhao(talhao)
    now = timezone.now()
    items = []

    for line in lines:
        parsed = parse_tracker_line(line, current_nmea_date)
        if not parsed:
            continue

        if parsed.get("date_str"):
            current_nmea_date = parsed.get("date_str")

        items.append(
            TalhaoChild(
                talhao=talhao,
                sentence_type=parsed["sentence_type"],
                raw_line=line,
                latitude=parsed.get("latitude"),
                longitude=parsed.get("longitude"),
                speed=parsed.get("speed"),
                satellites=parsed.get("satellites"),
                happened_at=parsed.get("happened_at"),
                created_at=now,
                status=1,
            )
        )

    if items:
        TalhaoChild.objects.bulk_create(items, batch_size=1000)
        total_saved = len(items)

    return total_saved


def get_last_nmea_date_for_talhao(talhao):
    last_with_time = (
        TalhaoChild.objects.filter(talhao=talhao)
        .exclude(happened_at__isnull=True)
        .order_by("-happened_at")
        .first()
    )
    if not last_with_time or not last_with_time.happened_at:
        return None

    return last_with_time.happened_at.strftime("%d%m%y")


def parse_tracker_line(line, current_nmea_date=None):
    parsed_json = parse_json_tracker_line(line)
    if parsed_json:
        return parsed_json

    return parse_nmea_line(line, current_nmea_date)


def parse_nmea_line(line, current_nmea_date=None):
    parts = line.split(",")
    if not parts or not parts[0].startswith("$GN"):
        return None

    sentence_type = parts[0][3:]

    if sentence_type == "GGA":
        happened_at = parse_nmea_datetime(parts[1] if len(parts) > 1 else None, current_nmea_date)
        return {
            "sentence_type": sentence_type,
            "latitude": parse_coordinate(parts[2] if len(parts) > 2 else None, parts[3] if len(parts) > 3 else None),
            "longitude": parse_coordinate(parts[4] if len(parts) > 4 else None, parts[5] if len(parts) > 5 else None),
            "satellites": safe_int(parts[7] if len(parts) > 7 else None),
            "speed": None,
            "happened_at": happened_at,
            "date_str": current_nmea_date,
        }

    if sentence_type == "RMC":
        date_str = parts[9] if len(parts) > 9 and parts[9] else None
        happened_at = parse_nmea_datetime(parts[1] if len(parts) > 1 else None, date_str)
        return {
            "sentence_type": sentence_type,
            "latitude": parse_coordinate(parts[3] if len(parts) > 3 else None, parts[4] if len(parts) > 4 else None),
            "longitude": parse_coordinate(parts[5] if len(parts) > 5 else None, parts[6] if len(parts) > 6 else None),
            "satellites": None,
            "speed": parts[7] if len(parts) > 7 and parts[7] else None,
            "happened_at": happened_at,
            "date_str": date_str,
        }

    return {
        "sentence_type": sentence_type,
        "latitude": None,
        "longitude": None,
        "satellites": None,
        "speed": None,
        "happened_at": None,
        "date_str": current_nmea_date,
    }


def parse_json_tracker_line(line):
    if not line or not line.startswith("{"):
        return None

    try:
        payload = json.loads(line)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None

    lat = payload.get("lat")
    lon = payload.get("lon")
    if lat in (None, "") or lon in (None, ""):
        return None

    happened_at = parse_json_tracker_datetime(payload.get("ts"))

    return {
        "sentence_type": "JSON",
        "latitude": safe_float_str(lat),
        "longitude": safe_float_str(lon),
        "satellites": safe_int(payload.get("sats")),
        "speed": safe_float(payload.get("spd")),
        "happened_at": happened_at,
        "date_str": happened_at.strftime("%d%m%y") if happened_at else None,
    }


def parse_coordinate(value, hemisphere):
    if not value or not hemisphere:
        return None

    try:
        numeric_value = float(value)
        degrees = int(numeric_value / 100)
        minutes = numeric_value - (degrees * 100)
        decimal = degrees + (minutes / 60)

        if hemisphere in ("S", "W"):
            decimal *= -1

        return f"{decimal:.8f}"
    except (TypeError, ValueError):
        return None


def parse_json_tracker_datetime(value):
    if not value:
        return None

    try:
        base = datetime.strptime(str(value), "%d-%m-%y_%H-%M-%S")
        return timezone.make_aware(base, timezone.get_current_timezone())
    except (TypeError, ValueError):
        return None


def parse_nmea_datetime(time_str, date_str=None):
    if not time_str:
        return None

    try:
        if "." in time_str:
            time_str = time_str.split(".")[0]

        if date_str:
            base = datetime.strptime(f"{date_str}{time_str}", "%d%m%y%H%M%S")
        else:
            now = timezone.localtime()
            only_time = datetime.strptime(time_str, "%H%M%S").time()
            base = datetime.combine(now.date(), only_time)

        return timezone.make_aware(base, timezone.get_current_timezone())
    except (TypeError, ValueError):
        return None


def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_float_str(value):
    numeric = safe_float(value)
    if numeric is None:
        return None
    return f"{numeric:.8f}"
