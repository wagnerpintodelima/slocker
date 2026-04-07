import json
import logging
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Count, Max
from django.shortcuts import redirect, render
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from app.models import TrackerImportJob
from backend.models import Talhao, TalhaoChild
from backend.services.tracker_jobs import TALHAO_STATUS_PROCESSED, process_tracker_file, mark_talhao_error

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

        if settings.DEBUG:
            job = TrackerImportJob.objects.filter(talhao_id=talhao.id).order_by("-id").first()
            try:
                total_saved = process_tracker_file(talhao.id, default_storage.path(file_name))
                if job:
                    job.status = TrackerImportJob.STATUS_DONE
                    job.total_saved = total_saved
                    job.started_at = timezone.now()
                    job.finished_at = timezone.now()
                    job.error_message = ""
                    job.attempts = (job.attempts or 0) + 1
                    job.save(update_fields=["status", "total_saved", "started_at", "finished_at", "error_message", "attempts", "updated_at"])
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    f"Upload processado localmente com sucesso. {total_saved} linha(s) importadas.",
                )
                logger.info("Job do tracker processado localmente. talhao_id=%s total_saved=%s", talhao.id, total_saved)
            except Exception as exc:
                mark_talhao_error(talhao.id)
                if job:
                    job.status = TrackerImportJob.STATUS_ERROR
                    job.error_message = str(exc)
                    job.started_at = timezone.now()
                    job.finished_at = timezone.now()
                    job.attempts = (job.attempts or 0) + 1
                    job.save(update_fields=["status", "error_message", "started_at", "finished_at", "attempts", "updated_at"])
                logger.exception("Erro ao processar upload do tracker localmente")
                messages.add_message(request, messages.ERROR, f"Erro ao processar arquivo localmente: {exc}")
                return redirect("TrackerIndexView")

        if not settings.DEBUG:
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

    delta_time = "--:--:--"
    max_speed = "0.00"
    total_points = 0

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

        stats = talhao_points.aggregate(total_points=Count("id"), max_speed=Max("speed"))
        total_points = stats.get("total_points") or 0
        if stats.get("max_speed") is not None:
            max_speed = f"{float(stats['max_speed']):.2f}"

    context = {
        "data": talhaos,
        "talhao": talhao,
        "delta_time": delta_time,
        "max_speed": max_speed,
        "total_points": total_points,
        "points_chunk_size": 500,
    }

    return render(request, "Tracker/mapa.html", context)


@login_required
def mapPointsView(request):
    talhao_id = request.GET.get("talhao_id")

    if not talhao_id:
        return JsonResponse({"status": 400, "description": "talhao_id e obrigatorio"}, status=400)

    try:
        offset = max(int(request.GET.get("offset", 0)), 0)
    except (TypeError, ValueError):
        offset = 0

    try:
        limit = int(request.GET.get("limit", 500))
    except (TypeError, ValueError):
        limit = 500

    limit = min(max(limit, 1), 2000)

    talhao = Talhao.objects.filter(id=talhao_id, status=TALHAO_STATUS_PROCESSED).first()
    if not talhao:
        return JsonResponse({"status": 404, "description": "Talhao nao encontrado"}, status=404)

    base_qs = TalhaoChild.objects.filter(
        talhao=talhao,
        latitude__isnull=False,
        longitude__isnull=False,
        status=1,
    ).order_by("id")

    total_points = base_qs.count()
    rows = list(
        base_qs[offset:offset + limit].values(
            "latitude",
            "longitude",
            "sentence_type",
            "speed",
            "satellites",
            "happened_at",
        )
    )

    points = [
        {
            "lat": float(item["latitude"]),
            "lng": float(item["longitude"]),
            "type": item["sentence_type"],
            "speed": item["speed"],
            "satellites": item["satellites"],
            "happened_at": item["happened_at"].strftime("%d/%m/%Y %H:%M:%S") if item["happened_at"] else "",
        }
        for item in rows
        if item["latitude"] and item["longitude"]
    ]

    next_offset = offset + len(points)

    return JsonResponse(
        {
            "status": 200,
            "points": points,
            "offset": offset,
            "next_offset": next_offset,
            "limit": limit,
            "total_points": total_points,
            "has_more": next_offset < total_points,
        }
    )


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
