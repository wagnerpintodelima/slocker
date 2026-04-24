import math

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.models import Talhao, TalhaoChild


EARTH_RADIUS_METERS = 6371000


def calculate_distance_meters(first_point, second_point):
    first_lat = math.radians(first_point[0])
    second_lat = math.radians(second_point[0])
    delta_lat = math.radians(second_point[0] - first_point[0])
    delta_lng = math.radians(second_point[1] - first_point[1])

    a = (
        math.sin(delta_lat / 2) * math.sin(delta_lat / 2)
        + math.cos(first_lat)
        * math.cos(second_lat)
        * math.sin(delta_lng / 2)
        * math.sin(delta_lng / 2)
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_METERS * c


def parse_coordinate(value):
    if value in (None, ""):
        return None

    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def calculate_talhao_distance(talhao):
    rows = (
        TalhaoChild.objects.filter(
            talhao=talhao,
            latitude__isnull=False,
            longitude__isnull=False,
            status=1,
        )
        .order_by("id")
        .values_list("latitude", "longitude")
    )

    previous_point = None
    total_meters = 0
    valid_points = 0

    for latitude, longitude in rows.iterator(chunk_size=2000):
        point = (parse_coordinate(latitude), parse_coordinate(longitude))

        if point[0] is None or point[1] is None:
            continue

        valid_points += 1

        if previous_point:
            total_meters += calculate_distance_meters(previous_point, point)

        previous_point = point

    return total_meters / 1000, valid_points


class Command(BaseCommand):
    help = "Calcula a distancia percorrida por talhao e salva em talhao.trip_distance."

    def add_arguments(self, parser):
        parser.add_argument("--talhao-id", type=int, help="Calcula somente um talhao.")
        parser.add_argument("--dry-run", action="store_true", help="Calcula sem salvar no banco.")

    def handle(self, *args, **options):
        talhao_id = options.get("talhao_id")
        dry_run = options["dry_run"]

        talhaos = Talhao.objects.all().order_by("id")
        if talhao_id:
            talhaos = talhaos.filter(id=talhao_id)

        total_talhoes = 0

        for talhao in talhaos:
            trip_distance, valid_points = calculate_talhao_distance(talhao)
            total_talhoes += 1

            if not dry_run:
                with transaction.atomic():
                    Talhao.objects.filter(id=talhao.id).update(trip_distance=trip_distance)

            self.stdout.write(
                f"Talhao #{talhao.id} - {talhao.name}: "
                f"{trip_distance:.3f} km ({valid_points} ponto(s))"
                f"{' [dry-run]' if dry_run else ''}"
            )

        if total_talhoes == 0:
            self.stdout.write(self.style.WARNING("Nenhum talhao encontrado."))
            return

        self.stdout.write(self.style.SUCCESS(f"{total_talhoes} talhao(s) processado(s)."))
