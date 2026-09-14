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
from urllib.parse import quote, urlsplit

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


def github_apk_response(version):
    token = getattr(settings, 'AGROLINE_GITHUB_TOKEN', '').strip()
    if not token:
        raise ValueError('Configure AGROLINE_GITHUB_TOKEN no settings.py.')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', REPOSITORY):
        raise ValueError('Repositorio GitHub invalido.')
    headers = {
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/vnd.github+json',
    }
    api = 'https://api.github.com/repos/' + REPOSITORY
    with requests.get(api + '/releases/tags/' + quote(version, safe=''),
                      headers=headers, timeout=(15, 60), allow_redirects=False) as release:
        if release.status_code == 404:
            release_data = None
        elif release.status_code != 200:
            raise ValueError('Consulta da release: HTTP {}. Confira token, permissao Contents: Read e tag.'.format(release.status_code))
        else:
            release_data = release.json()
    # Lookup by tag only returns published releases. Authenticated listing can
    # include drafts visible to the token's account.
    page = 1
    while release_data is None:
        with requests.get(api + '/releases', headers=headers,
                          params={'per_page': 100, 'page': page},
                          timeout=(15, 60), allow_redirects=False) as listing:
            if listing.status_code != 200:
                raise ValueError('Consulta de rascunhos: HTTP {}'.format(listing.status_code))
            releases = listing.json()
        release_data = next((r for r in releases if r.get('tag_name') == version), None)
        if release_data is None and len(releases) < 100:
            raise ValueError('Release nao encontrada; confira a tag e o acesso do token aos rascunhos.')
        page += 1
    assets = [a for a in release_data.get('assets', [])
              if a.get('name') == 'AgroLine.apk' and a.get('state') == 'uploaded']
    if len(assets) != 1:
        raise ValueError('A release precisa conter um asset AgroLine.apk pronto para download.')
    asset_url = api + '/releases/assets/' + str(int(assets[0]['id']))
    headers['Accept'] = 'application/octet-stream'
    response = requests.get(asset_url, headers=headers, stream=True,
                            timeout=(15, 120), allow_redirects=False)
    if response.status_code in (301, 302, 303, 307, 308):
        location = response.headers.get('Location', '')
        response.close()
        parsed = urlsplit(location)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Redirecionamento de download invalido.')
        # The signed asset URL authenticates itself. Never forward the PAT to storage.
        response = requests.get(location, stream=True, timeout=(15, 120))
    if response.status_code != 200:
        status = response.status_code
        response.close()
        raise ValueError('Download do APK: HTTP {}'.format(status))
    return response


def import_release(version, description='', action='published'):
    if parse_version(version) is None:
        log_update(f'Versão inválida: {version!r}. Esperado vX.Y.Z.')
        return
    
    # Serializes downloads in this process; database lock below covers other workers.
    with _lock:
        close_old_connections()
        final_zip = None
        registered = False
        old_zip = None
        try:
            existed_before_download = False
            if action == 'edited':
                existed_before_download = AtronUpdate.objects.filter(version_current=version).exists()
                if not existed_before_download:
                    if not newer_than_registered(version):
                        return
                    log_update(f'{version}: edicao de versao nova; sera cadastrada com status=0.')
            elif not newer_than_registered(version):
                return
            log_update(f'Baixando AgroLine.apk de {REPOSITORY}, release {version}, pela API GitHub.')
            folder = Path(settings.MEDIA_ROOT) / 'backend/upload/atron/update/apk'
            folder.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='github-', dir=folder) as work:
                apk = Path(work) / 'AgroLine.apk'
                with github_apk_response(version) as response:
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
                    item = None
                    if action == 'edited':
                        item = AtronUpdate.objects.select_for_update().filter(version_current=version).order_by('-id').first()
                        if item is None:
                            if existed_before_download:
                                log_update(f'{version}: registro removido durante o download; edicao cancelada.')
                                return
                            if not newer_than_registered(version):
                                return
                        else:
                            old_zip = (folder / (item.apk + '.zip')).resolve()
                            if old_zip.parent != folder.resolve():
                                raise ValueError('Caminho do ZIP anterior fora da pasta de updates.')
                    elif not newer_than_registered(version):
                        return
                    name = f'AgroLine-{version}-{uuid.uuid4().hex}'
                    final_zip = folder / (name + '.zip')
                    shutil.move(str(packaged), str(final_zip))
                    now = timezone.now()
                    actor = int(os.getenv('AGROLINE_GITHUB_USER_ID', '0'))
                    if item is not None:
                        item.description = description
                        item.apk = name
                        item.updated_at = now
                        item.updated_by = actor
                        item.save(update_fields=['description', 'apk', 'updated_at', 'updated_by'])
                    else:
                        AtronUpdate.objects.create(
                            version_current=version, description=description,
                            apk=name, level=0, status=0, created_at=now, updated_at=now,
                            created_by=actor, updated_by=actor,
                        )
                registered = True
                if old_zip is not None:
                    try:
                        if not AtronUpdate.objects.filter(apk=old_zip.stem).exists():
                            try:
                                old_zip.unlink()
                            except FileNotFoundError:
                                pass
                        else:
                            log_update('ZIP anterior ainda usado por outro registro; arquivo preservado.')
                    except Exception as exc:
                        log_update(f'{version}: novo ZIP salvo, mas falhou a limpeza do anterior: {exc}')
                    log_update(f'{version}: APK baixado novamente, ZIP e descricao atualizados. Status mantido.')
                else:
                    log_update(f'{version} cadastrada com status=0. ZIP: {final_zip.name}')
        except Exception as exc:
            log_update(f'Falha ao importar {version}: {exc}')
        finally:
            if final_zip is not None and not registered:
                try:
                    final_zip.unlink()
                except FileNotFoundError:
                    pass
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
