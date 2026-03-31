from pathlib import Path
import logging
import time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.models import TrackerImportJob
from backend.services.tracker_jobs import mark_talhao_error, process_tracker_file

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Processa a fila de importacao do tracker."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Processa um job e encerra.")
        parser.add_argument("--sleep", type=int, default=5, help="Intervalo entre varreduras da fila.")

    def handle(self, *args, **options):
        run_once = options["once"]
        sleep_seconds = max(options["sleep"], 1)

        logger.info("Worker da fila do tracker iniciado. once=%s sleep=%s", run_once, sleep_seconds)
        self.stdout.write(self.style.SUCCESS("Worker da fila do tracker iniciado."))

        while True:
            processed = self.process_next_job()

            if run_once:
                break

            if not processed:
                time.sleep(sleep_seconds)

    def process_next_job(self):
        with transaction.atomic():
            job = (
                TrackerImportJob.objects.select_for_update(skip_locked=True)
                .filter(status=TrackerImportJob.STATUS_PENDING)
                .order_by("created_at")
                .first()
            )

            if not job:
                return False

            job.status = TrackerImportJob.STATUS_PROCESSING
            job.started_at = timezone.now()
            job.finished_at = None
            job.attempts += 1
            job.error_message = ""
            job.save(update_fields=["status", "started_at", "finished_at", "attempts", "error_message", "updated_at"])

        try:
            logger.info("Processando job do tracker. job_id=%s talhao_id=%s arquivo=%s", job.id, job.talhao_id, job.file_path)
            total_saved = process_tracker_file(job.talhao_id, job.file_path)
            job.status = TrackerImportJob.STATUS_DONE
            job.total_saved = total_saved
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "total_saved", "finished_at", "updated_at"])

            if job.file_path:
                file_to_remove = Path(job.file_path)
                if file_to_remove.exists():
                    file_to_remove.unlink()

            logger.info("Job do tracker concluido. job_id=%s total_saved=%s", job.id, total_saved)
            self.stdout.write(self.style.SUCCESS(f"Job {job.id} concluido com {total_saved} linha(s)."))
        except Exception as exc:
            mark_talhao_error(job.talhao_id)
            job.status = TrackerImportJob.STATUS_ERROR
            job.error_message = str(exc)
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "error_message", "finished_at", "updated_at"])
            logger.exception("Job do tracker falhou. job_id=%s talhao_id=%s", job.id, job.talhao_id)
            self.stderr.write(self.style.ERROR(f"Job {job.id} falhou: {exc}"))

        return True
