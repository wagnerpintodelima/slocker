import datetime
import json
import logging
import time

import paho.mqtt.client as mqtt
from django.conf import settings
from backend.services.tracker_jobs import append_tracker_package


logger = logging.getLogger(__name__)


class MqttListenerService:
    PACKAGE_LIMIT = 150
    MAX_RETRIES_PER_PACKAGE = 3
    AUTOMATIONS_TOPICS = [
        {
            "name": "smx-000-001",
            "topic_uc_to_broker": "/smx-000-001/uc/to/broker",
            "topic_broker_to_uc": "/smx-000-001/broker/to/uc",
        },
    ]

    def __init__(self):
        self.broker_host = settings.MQTT_BROKER_HOST
        self.broker_port = settings.MQTT_BROKER_PORT
        self.username = settings.MQTT_USERNAME
        self.password = settings.MQTT_PASSWORD
        self.base_url = settings.MQTT_OPERATIONS_BASE_URL.rstrip("/")
        self.automations_topics = self.build_automations_topics()
        self.topic_map = {
            item["topic_uc_to_broker"]: item for item in self.automations_topics
        }
        self.sync_state = {}
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def build_automations_topics(self):
        topics = []
        for item in self.AUTOMATIONS_TOPICS:
            topics.append(
                {
                    "name": item["name"],
                    "topic_uc_to_broker": item["topic_uc_to_broker"],
                    "topic_broker_to_uc": item["topic_broker_to_uc"],
                }
            )
        return topics

    def emit(self, message, level="info"):
        clean_message = str(message).rstrip()
        try:
            print(clean_message)
        except Exception:
            pass

        try:
            log_method = getattr(logger, level, logger.info)
            for line in clean_message.splitlines():
                log_method(line)
        except Exception:
            pass

    def emit_block(self, title, lines, level="info"):
        block_lines = [
            "",
            "=" * 90,
            title,
            "-" * 90,
        ]
        block_lines.extend(str(line) for line in lines)
        block_lines.append("=" * 90)
        self.emit("\n".join(block_lines), level=level)

    def run_forever(self, reconnect_delay=5):
        reconnect_delay = max(int(reconnect_delay), 1)

        while True:
            try:
                logger.info(
                    "Iniciando listener MQTT. broker=%s:%s subscriptions=%s",
                    self.broker_host,
                    self.broker_port,
                    len(self.automations_topics),
                )
                self.client.connect(self.broker_host, self.broker_port)
                self.client.loop_forever()
            except KeyboardInterrupt:
                logger.info("Listener MQTT interrompido manualmente.")
                raise
            except Exception:
                logger.exception("Falha no loop principal do listener MQTT. Nova tentativa em %s segundo(s).", reconnect_delay)
                time.sleep(reconnect_delay)

    def on_connect(self, client, userdata, flags, rc):
        logger.info("MQTT conectado. rc=%s", rc)
        for item in self.automations_topics:
            client.subscribe(item["topic_uc_to_broker"], 0)
            logger.info(
                "MQTT inscrito. automation=%s topic=%s",
                item["name"],
                item["topic_uc_to_broker"],
            )

    def on_disconnect(self, client, userdata, rc):
        logger.warning("MQTT desconectado. rc=%s", rc)

    def on_message(self, client, userdata, msg):
        now = datetime.datetime.now()
        automation_config = self.topic_map.get(msg.topic)

        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)
        except Exception:
            self.emit(
                f"Payload descartado por falha ao decodificar JSON UTF-8. topic={msg.topic}",
                level="warning",
            )
            if automation_config:
                self.retry_pending_package(automation_config)
            return

        logger.info("Mensagem MQTT recebida. topic=%s", msg.topic)

        if not automation_config:
            logger.warning("Topico ignorado pelo listener principal. topic=%s", msg.topic)
            return

        try:
            self.handle_payload(data, now, automation_config)
        except Exception:
            logger.exception("Falha ao processar mensagem MQTT. payload=%s", payload)

    def handle_payload(self, data, now, automation_config):
        message_type = str(data.get("type", "")).strip().lower()

        if message_type == "sync_inventory" or isinstance(data.get("files"), list):
            self.handle_sync_inventory(data, automation_config)
            return

        if isinstance(data.get("data"), list) and "path" in data:
            self.handle_sync_package_response(data, automation_config)
            return

        self.emit(
            f"Nenhuma rotina de sync aplicada para automation={automation_config['name']}.",
            level="info",
        )

    def handle_sync_inventory(self, data, automation_config):
        files = data.get("files") or []
        normalized_files = []

        for item in files:
            path = item.get("path")
            registers = item.get("registers", 0)
            if not path:
                continue

            normalized_files.append(
                {
                    "path": path,
                    "registers": int(registers or 0),
                }
            )

        self.sync_state[automation_config["name"]] = {
            "files": normalized_files,
            "current_file_index": 0,
            "pending_path": None,
            "pending_offset": 0,
            "pending_limit": self.PACKAGE_LIMIT,
            "pending_retries": 0,
            "current_talhao_id": None,
        }

        self.emit_block(
            f"SYNC INVENTORY | {automation_config['name']}",
            [
                f"Arquivos recebidos: {len(normalized_files)}",
                "Lista:",
                *[
                    f"[{index}] path={item['path']} registers={item['registers']}"
                    for index, item in enumerate(normalized_files)
                ],
            ],
        )

        self.request_next_package(automation_config)

    def handle_sync_package_response(self, data, automation_config):
        state = self.sync_state.get(automation_config["name"])
        if not state:
            self.emit(
                f"Resposta de pacote recebida sem inventario ativo para {automation_config['name']}.",
                level="warning",
            )
            return

        current_file = self.get_current_file_state(automation_config)
        if not current_file:
            self.emit(
                f"Resposta de pacote recebida sem arquivo atual para {automation_config['name']}.",
                level="warning",
            )
            return

        expected_path = state.get("pending_path")
        expected_offset = int(state.get("pending_offset", 0) or 0)
        current_index = int(state.get("current_file_index", 0) or 0)
        if not expected_path:
            self.emit_block(
                f"SYNC RESPONSE DESCARTADA | {automation_config['name']}",
                [
                    "Motivo: resposta sem pacote pendente.",
                    f"current_file_index={current_index}",
                    f"response_path={data.get('path')}",
                    f"response_offset={data.get('offset')}",
                ],
                level="warning",
            )
            return

        response_path = data.get("path")
        if response_path != expected_path:
            self.emit_block(
                f"SYNC RESPONSE DESCARTADA | {automation_config['name']}",
                [
                    "Motivo: path diferente do esperado.",
                    f"current_file_index={current_index}",
                    f"expected_path={expected_path}",
                    f"received_path={response_path}",
                    f"expected_offset={expected_offset}",
                    f"received_offset={data.get('offset')}",
                ],
                level="warning",
            )
            return

        offset = int(data.get("offset", 0) or 0)
        count = int(data.get("count", 0) or 0)
        has_more = bool(data.get("has_more"))
        next_offset = offset + count

        if offset != expected_offset:
            self.emit_block(
                f"SYNC RESPONSE DESCARTADA | {automation_config['name']}",
                [
                    "Motivo: offset diferente do esperado.",
                    f"current_file_index={current_index}",
                    f"expected_path={expected_path}",
                    f"received_path={response_path}",
                    f"expected_offset={expected_offset}",
                    f"received_offset={offset}",
                ],
                level="warning",
            )
            return

        state["pending_path"] = None
        state["pending_retries"] = 0
        talhao, total_saved = append_tracker_package(
            file_path=response_path,
            lines=data.get("data") or [],
            clear_existing=(offset == 0),
        )
        state["current_talhao_id"] = getattr(talhao, "id", None)

        self.emit_block(
            f"SYNC RESPONSE OK | {automation_config['name']}",
            [
                f"current_file_index={current_index}",
                f"talhao_id={state['current_talhao_id']}",
                f"path={response_path}",
                f"offset={offset}",
                f"count={count}",
                f"saved={total_saved}",
                f"has_more={has_more}",
                f"next_offset={next_offset}",
            ],
        )

        if has_more:
            self.request_package(
                automation_config=automation_config,
                path=response_path,
                offset=next_offset,
                limit=self.PACKAGE_LIMIT,
            )
            return

        self.emit_block(
            f"SYNC FILE DONE | {automation_config['name']}",
            [
                f"Arquivo concluido: {response_path}",
                f"current_file_index antes do incremento={current_index}",
                "Proximo passo real esperado: avisar UC para excluir o arquivo.",
            ],
        )
        state["current_file_index"] += 1
        self.emit_block(
            f"SYNC NEXT FILE | {automation_config['name']}",
            [
                f"current_file_index depois do incremento={state['current_file_index']}",
            ],
        )
        self.request_next_package(automation_config)

    def request_next_package(self, automation_config):
        current_file = self.get_current_file_state(automation_config)
        state = self.sync_state.get(automation_config["name"]) or {}

        if not current_file:
            self.emit_block(
                f"SYNC FINISHED | {automation_config['name']}",
                [
                    "Nenhum arquivo pendente.",
                    f"current_file_index={state.get('current_file_index')}",
                    f"total_files={len(state.get('files') or [])}",
                ],
            )
            return

        self.emit_block(
            f"SYNC REQUEST NEXT | {automation_config['name']}",
            [
                f"current_file_index={state.get('current_file_index')}",
                f"path={current_file['path']}",
                f"registers={current_file['registers']}",
                f"offset=0",
                f"limit={self.PACKAGE_LIMIT}",
            ],
        )
        self.request_package(
            automation_config=automation_config,
            path=current_file["path"],
            offset=0,
            limit=self.PACKAGE_LIMIT,
        )

    def get_current_file_state(self, automation_config):
        state = self.sync_state.get(automation_config["name"])
        if not state:
            return None

        current_index = state.get("current_file_index", 0)
        files = state.get("files") or []

        if current_index < 0 or current_index >= len(files):
            return None

        return files[current_index]

    def request_package(self, automation_config, path, offset, limit, reset_retry=True): 
        state = self.sync_state.setdefault(
            automation_config["name"],
            {
                "files": [],
                "current_file_index": 0,
                "pending_path": None,
                "pending_offset": 0,
                "pending_limit": self.PACKAGE_LIMIT,
                "pending_retries": 0,
                "current_talhao_id": None,
            },
        )
        state["pending_path"] = path
        state["pending_offset"] = offset
        state["pending_limit"] = limit
        if reset_retry:
            state["pending_retries"] = 0

        payload = {
            "type": "sync_broker_load_package",
            "path": path,
            "offset": offset,
            "limit": limit,
        }
        self.emit(
            (
                f"Solicitando pacote para {automation_config['name']}: "
                f"path={path} offset={offset} limit={limit}"
            )
        )
        self.publish(payload, automation_config["topic_broker_to_uc"])

    def retry_pending_package(self, automation_config):
        state = self.sync_state.get(automation_config["name"])
        current_file = self.get_current_file_state(automation_config)

        if not state or not current_file:
            self.emit(
                f"Nao existe pacote pendente para repetir em {automation_config['name']}.",
                level="warning",
            )
            return

        pending_path = state.get("pending_path")
        if not pending_path:
            self.emit(
                f"Nao existe path pendente para repetir em {automation_config['name']}.",
                level="warning",
            )
            return

        offset = int(state.get("pending_offset", 0) or 0)
        limit = int(state.get("pending_limit", self.PACKAGE_LIMIT) or self.PACKAGE_LIMIT)
        retries = int(state.get("pending_retries", 0) or 0) + 1
        state["pending_retries"] = retries

        if retries > self.MAX_RETRIES_PER_PACKAGE:
            self.emit_block(
                f"SYNC SKIP FILE | {automation_config['name']}",
                [
                    "Limite de retries por pacote atingido.",
                    f"path={pending_path}",
                    f"offset={offset}",
                    f"limit={limit}",
                    f"retry={retries}/{self.MAX_RETRIES_PER_PACKAGE}",
                    "Arquivo atual sera abandonado e o fluxo seguira para o proximo.",
                ],
                level="warning",
            )
            state["pending_path"] = None
            state["pending_retries"] = 0
            state["current_file_index"] = int(state.get("current_file_index", 0) or 0) + 1
            self.request_next_package(automation_config)
            return

        self.emit_block(
            f"SYNC RETRY | {automation_config['name']}",
            [
                f"path={pending_path}",
                f"offset={offset}",
                f"limit={limit}",
                f"current_file_index={state.get('current_file_index')}",
                f"retry={retries}/{self.MAX_RETRIES_PER_PACKAGE}",
            ],
            level="warning",
        )
        self.request_package(
            automation_config=automation_config,
            path=pending_path,
            offset=offset,
            limit=limit,
            reset_retry=False,
        )

    def publish(self, payload, topic):
        message = json.dumps(payload)
        result = self.client.publish(topic, message)
        logger.info("Mensagem MQTT publicada. topic=%s mid=%s", topic, getattr(result, "mid", None))
