import json
import logging
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from app.models import TrackerImportJob
from backend.models import Talhao, TalhaoChild
from backend.services.tracker_jobs import TALHAO_STATUS_PROCESSED

logger = logging.getLogger(__name__)


@login_required
def indexView(request):
    talhaos = Talhao.objects.order_by("-created_at")
    talhao_ids = [item.id for item in talhaos]
    jobs_by_talhao = {}
    points_by_talhao = {
        item["talhao"]: item["total_points"]
        for item in TalhaoChild.objects.filter(talhao_id__in=talhao_ids, status=1)
        .values("talhao")
        .annotate(total_points=Count("id"))
    }
    for job in TrackerImportJob.objects.filter(talhao_id__in=talhao_ids).order_by("-created_at"):
        if job.talhao_id not in jobs_by_talhao:
            jobs_by_talhao[job.talhao_id] = job

    context = {
        "data": [
            {
                "item": talhao,
                "job": jobs_by_talhao.get(talhao.id),
                "total_points": points_by_talhao.get(talhao.id, 0),
                "estimated_time": _format_points_time(points_by_talhao.get(talhao.id, 0)),
            }
            for talhao in talhaos
        ]
    }

    return render(request, "Tracker/index.html", context)


@login_required
def newView(request):
    context = {
        "data": None
    }

    return render(request, "Tracker/new.html", context)


@login_required
@require_http_methods(["POST"])
def newAction(request):
    name = request.POST.get("talhao", "").strip()
    file = request.FILES.get("file")

    if not file:
        messages.add_message(request, messages.ERROR, "Selecione um arquivo .txt para importar.")
        return redirect("TrackerNewView")

    try:
        logger.info("Recebendo upload do tracker. user_id=%s arquivo=%s", getattr(request.user, "id", None), getattr(file, "name", None))
        file_name = default_storage.save(
            f'tracker_uploads/{timezone.now().strftime("%Y%m%d%H%M%S")}_{file.name}',
            ContentFile(file.read()),
        )

        talhao = Talhao()
        talhao.name = name or file.name
        talhao.created_at = timezone.now()
        talhao.status = 0
        talhao.save()

        TrackerImportJob.objects.create(
            talhao_id=talhao.id,
            file_path=default_storage.path(file_name),
            original_name=file.name,
            status=TrackerImportJob.STATUS_PENDING,
        )

        messages.add_message(
            request,
            messages.SUCCESS,
            "Upload recebido. O arquivo foi enviado para a fila de processamento.",
        )
        logger.info("Job do tracker enfileirado com sucesso. talhao_id=%s arquivo=%s", talhao.id, file_name)
    except Exception as exc:
        logger.exception("Erro ao enfileirar arquivo do tracker")
        messages.add_message(request, messages.ERROR, f"Erro ao enfileirar arquivo: {exc}")

    return redirect("TrackerIndexView")


@login_required
def mapView(request):
    talhaos = Talhao.objects.filter(status=TALHAO_STATUS_PROCESSED).order_by("-created_at")
    talhao_id = request.GET.get("talhao_id")
    talhao = None

    if talhao_id:
        talhao = talhaos.filter(id=talhao_id).first()

    if not talhao:
        talhao = talhaos.first()

    points = []
    delta_time = "--:--:--"
    max_speed = "0.00"

    if talhao:
        talhao_points = TalhaoChild.objects.filter(
            talhao=talhao,
            latitude__isnull=False,
            longitude__isnull=False,
            status=1,
        ).order_by("id")

        first_point_with_time = talhao_points.exclude(happened_at__isnull=True).first()
        last_point_with_time = talhao_points.exclude(happened_at__isnull=True).last()

        if first_point_with_time and last_point_with_time:
            delta_time = _format_timedelta(last_point_with_time.happened_at - first_point_with_time.happened_at)

        valid_speeds = [float(item.speed) for item in talhao_points if item.speed is not None]
        if valid_speeds:
            max_speed = f"{max(valid_speeds):.2f}"

        points = [
            {
                "lat": float(item.latitude),
                "lng": float(item.longitude),
                "type": item.sentence_type,
                "speed": item.speed,
                "satellites": item.satellites,
                "happened_at": item.happened_at.strftime("%d/%m/%Y %H:%M:%S") if item.happened_at else "",
            }
            for item in talhao_points
            if item.latitude and item.longitude
        ]

    context = {
        "data": talhaos,
        "talhao": talhao,
        "points_json": json.dumps(points),
        "delta_time": delta_time,
        "max_speed": max_speed,
    }

    return render(request, "Tracker/mapa.html", context)


@login_required
def deleteAction(request, talhao_id):
    file_paths = []

    try:
        logger.info("Solicitada exclusao de talhao do tracker. talhao_id=%s user_id=%s", talhao_id, getattr(request.user, "id", None))
        with transaction.atomic():
            talhao = Talhao.objects.get(id=int(talhao_id))
            jobs = list(TrackerImportJob.objects.filter(talhao_id=talhao.id))
            file_paths = [job.file_path for job in jobs if job.file_path]

            TrackerImportJob.objects.filter(talhao_id=talhao.id).delete()
            TalhaoChild.objects.filter(talhao=talhao).delete()
            talhao.delete()

        for file_path in file_paths:
            try:
                file_to_remove = Path(file_path)
                if file_to_remove.exists():
                    file_to_remove.unlink()
            except Exception:
                pass

        context = {
            "status": 200,
            "descricao": "Excluído com sucesso",
        }
    except Exception as exc:
        logger.exception("Erro ao excluir talhao do tracker. talhao_id=%s", talhao_id)
        context = {
            "status": 500,
            "description": str(exc),
        }

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json")


def _format_timedelta(delta):
    total_seconds = int(abs(delta.total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _format_points_time(total_points):
    total_minutes = round(total_points / 2)
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}"
