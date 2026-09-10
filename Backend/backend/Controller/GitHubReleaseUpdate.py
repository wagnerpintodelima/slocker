"""Importa uma release em background, sempre aguardando liberação manual."""
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
import uuid
import zipfile

import requests
from django.conf import settings
from django.db import close_old_connections, connection, transaction
from django.utils import timezone

from backend.models import AtronUpdate


REPOSITORY = os.getenv('AGROLINE_GITHUB_REPOSITORY', 'wagnerpintodelima/AgroLine')
_lock = threading.Lock()
_slots = threading.BoundedSemaphore(4)



def log_update(message):
    # Preserve Unicode on UTF-8 terminals, escape unsupported characters on ASCII.
    encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
    text = ('[GitHub update] ' + str(message)).encode(
        encoding, errors='backslashreplace').decode(encoding)
    print(text, flush=True)


def parse_version(version):
    if not isinstance(version, str) or len(version) > 30:
        return None
    match = re.fullmatch(r'v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version)
    return tuple(map(int, match.groups())) if match else None


def newer_than_registered(version):
    current = parse_version(version)
    for saved in AtronUpdate.objects.values_list('version_current', flat=True):
        parsed = parse_version(saved)
        if parsed is None:
            # Older manual records can omit the v prefix.
            parsed = parse_version('v' + saved) if isinstance(saved, str) else None
        if parsed is None:
            raise ValueError(f'Versão cadastrada inválida: {saved!r}; confira antes de importar.')
        if current <= parsed:
            log_update(f'{version} ignorada: já existe {saved}.')
            return False
    return True


def import_release(version, description='', action='published'):
    if parse_version(version) is None:
        log_update(f'Versão inválida: {version!r}. Esperado vX.Y.Z.')
        return
    
    # Serializes downloads in this process; database lock below covers other workers.
    with _lock:
        close_old_connections()
        final_zip = None
        registered = False
        try:
            if action == 'edited':
                count = AtronUpdate.objects.filter(version_current=version).update(description=description)
                log_update(f'{version}: descricao atualizada em {count} registro(s).')
                return
            if not newer_than_registered(version):
                return
            url = f'https://github.com/{REPOSITORY}/releases/download/{version}/AgroLine.apk'
            log_update(f'Baixando {url}')
            folder = Path(settings.MEDIA_ROOT) / 'backend/upload/atron/update/apk'
            folder.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='github-', dir=folder) as work:
                apk = Path(work) / 'AgroLine.apk'
                with requests.get(url, stream=True, timeout=(15, 120)) as response:
                    response.raise_for_status()
                    size = 0
                    with apk.open('wb') as output:
                        for chunk in response.iter_content(1024 * 1024):
                            size += len(chunk)
                            if size > 512 * 1024 * 1024:
                                raise ValueError('APK excede o limite de 512 MiB.')
                            output.write(chunk)
                with zipfile.ZipFile(apk) as archive:
                    if 'AndroidManifest.xml' not in archive.namelist() or archive.testzip():
                        raise ValueError('O download não contém um APK íntegro.')
                packaged = Path(work) / 'update.zip'
                with zipfile.ZipFile(packaged, 'w', zipfile.ZIP_DEFLATED) as archive:
                    archive.write(apk, 'AgroLine.apk')
                apk.unlink()
                with transaction.atomic():
                    if connection.vendor == 'postgresql':
                        with connection.cursor() as cursor:
                            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [714038201])
                    if not newer_than_registered(version):
                        return
                    name = f'AgroLine-{version}-{uuid.uuid4().hex}'
                    final_zip = folder / (name + '.zip')
                    shutil.move(str(packaged), str(final_zip))
                    now = timezone.now()
                    actor = int(os.getenv('AGROLINE_GITHUB_USER_ID', '0'))
                    AtronUpdate.objects.create(
                        version_current=version, description=description,
                        apk=name, level=0, status=0, created_at=now, updated_at=now,
                        created_by=actor, updated_by=actor,
                    )
                registered = True
                log_update(f'{version} cadastrada com status=0. ZIP: {final_zip.name}')
        except Exception as exc:
            log_update(f'Falha ao importar {version}: {exc}')
        finally:
            if final_zip is not None and not registered:
                final_zip.unlink(missing_ok=True)
            close_old_connections()


def start_release(version, description='', action='published'):
    if not _slots.acquire(blocking=False):
        return False

    def run(received_version, received_description, received_action):
        try:
            import_release(received_version, received_description, received_action)
        finally:
            _slots.release()

    worker = threading.Thread(target=run, args=(version, description, action),
                              name=f'github-release-{version}', daemon=True)
    try:
        worker.start()
    except Exception:
        _slots.release()
        raise
    return True
