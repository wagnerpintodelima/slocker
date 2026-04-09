import json
import logging
import time

import paho.mqtt.client as mqtt
from django.conf import settings

from backend.services.tracker_jobs import append_tracker_package


logger = logging.getLogger(__name__)


class MqttListenerService:
    PACKAGE_LIMIT = 150
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
        return list(self.AUTOMATIONS_TOPICS)

    def describe_connect_rc(self, rc):
        rc_map = {
            0: "conexao aceita",
            1: "versao de protocolo incorreta",
            2: "client id invalido",
            3: "servidor indisponivel",
            4: "usuario ou senha invalidos",
            5: "nao autorizado",
        }
        return rc_map.get(rc, "codigo desconhecido")

    def emit(self, message, level="info"):
        clean_message = str(message).rstrip()
        try:
            print(clean_message)
        except Exception:
            pass

        log_method = getattr(logger, level, logger.info)
        for line in clean_message.splitlines():
            log_method(line)

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
                logger.exception(
                    "Falha no loop principal do listener MQTT. Nova tentativa em %s segundo(s).",
                    reconnect_delay,
                )
                time.sleep(reconnect_delay)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT conectado com sucesso. rc=%s", rc)
        else:
            logger.warning("MQTT conectado com alerta. rc=%s descricao=%s", rc, self.describe_connect_rc(rc))

        if rc == 0:
            self.publish(
                {
                    "type": "broker_status",
                    "status": "online",
                    "message": "Broker online",
                },
                "/broadcast/broker/status",
            )
            logger.info("Broadcast de status publicado. topic=/broadcast/broker/status")

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
        raw_payload = msg.payload.decode("utf-8", errors="replace")
        automation_config = self.topic_map.get(msg.topic)

        if not automation_config:
            return

        if self.should_handle_as_raw_package(msg.topic, raw_payload, automation_config):
            self.handle_raw_package_response(raw_payload, automation_config)
            return

        try:
            data = json.loads(raw_payload)
        except Exception:
            logger.warning(
                "Payload MQTT invalido. automation=%s topic=%s",
                automation_config["name"],
                msg.topic,
            )
            return
        self.handle_payload(data, automation_config)

    def handle_payload(self, data, automation_config):
        if self.is_sync_inventory_payload(data):
            self.handle_sync_inventory(data, automation_config)
            return

        if self.is_sync_package_payload(data):
            self.handle_sync_package_response(data, automation_config)
            return

        self.emit_block(
            f"MQTT SEM ROTINA | {automation_config['name']}",
            [
                f"type={data.get('type')}",
                f"keys={sorted(list(data.keys()))}",
            ],
            level="warning",
        )

    def should_handle_as_raw_package(self, topic, raw_payload, automation_config):
        if topic != automation_config["topic_uc_to_broker"]:
            return False

        state = self.sync_state.get(automation_config["name"]) or {}
        if not state.get("pending_path"):
            return False

        lines = [line.strip() for line in raw_payload.splitlines() if line.strip()]
        if len(lines) <= 1:
            return False

        for line in lines:
            if not line.startswith("{"):
                return False
            try:
                parsed = json.loads(line)
            except Exception:
                return False

            if not isinstance(parsed, dict):
                return False

        return True

    def is_sync_inventory_payload(self, data):
        return str(data.get("type", "")).strip().lower() == "sync_inventory" or isinstance(
            data.get("files"), list
        )

    def is_sync_package_payload(self, data):
        return "path" in data and isinstance(self.get_sync_package_lines(data), list)

    def get_sync_package_lines(self, data):
        for key in ("data", "lines", "items", "records"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return []

    def handle_sync_inventory(self, data, automation_config):
        files = data.get("files") or []
        normalized_files = []

        for item in files:
            if not isinstance(item, dict):
                continue

            path = item.get("path")
            registers = int(item.get("registers", 0) or 0)
            if not path:
                continue

            normalized_files.append(
                {
                    "path": path,
                    "registers": registers,
                }
            )

        self.sync_state[automation_config["name"]] = {
            "files": normalized_files,
            "current_file_index": 0,
            "pending_path": None,
            "pending_offset": 0,
            "pending_limit": self.PACKAGE_LIMIT,
        }

        logger.info(
            "Inventario recebido. automation=%s folder=%s total_arquivos=%s",
            automation_config["name"],
            data.get("folder"),
            len(normalized_files),
        )

        if not normalized_files:
            error_payload = {
                "type": "sync_broker_error",
                "status": "error",
                "message": "Nenhum arquivo disponivel para sincronizacao",
                "folder": data.get("folder"),
                "total_files": 0,
            }
            logger.info(
                "Inventario vazio recebido. automation=%s folder=%s",
                automation_config["name"],
                data.get("folder"),
            )
            self.publish(error_payload, automation_config["topic_broker_to_uc"])
            logger.warning(
                "UC notificado sobre inventario vazio. automation=%s topic=%s",
                automation_config["name"],
                automation_config["topic_broker_to_uc"],
            )
            return

        self.request_next_package(automation_config)

    def handle_sync_package_response(self, data, automation_config):
        state = self.sync_state.get(automation_config["name"])
        if not state:
            self.emit_block(
                f"SYNC PACKAGE SEM ESTADO | {automation_config['name']}",
                [
                    "Nenhum inventario ativo encontrado.",
                    f"path={data.get('path')}",
                ],
                level="warning",
            )
            return

        package_lines = self.get_sync_package_lines(data)
        offset = int(data.get("offset", 0) or 0)
        count = int(data.get("count", len(package_lines)) or 0)
        has_more = bool(data.get("has_more"))
        path = data.get("path")

        logger.info(
            "Pacote JSON recebido. automation=%s path=%s offset=%s count=%s has_more=%s",
            automation_config["name"],
            path,
            offset,
            count,
            has_more,
        )

        state["pending_path"] = None

        if has_more:
            self.request_package(
                automation_config=automation_config,
                path=path,
                offset=offset + count,
                limit=self.PACKAGE_LIMIT,
            )
            return

        state["current_file_index"] += 1
        logger.info(
            "Arquivo sincronizado. automation=%s path=%s proximo_indice=%s",
            automation_config["name"],
            path,
            state["current_file_index"],
        )
        self.request_next_package(automation_config)

    def handle_raw_package_response(self, raw_payload, automation_config):
        state = self.sync_state.get(automation_config["name"])
        current_file = self.get_current_file_state(automation_config)

        if not state or not current_file:
            self.emit_block(
                f"SYNC RAW SEM ESTADO | {automation_config['name']}",
                [
                    "Pacote NDJSON recebido sem inventario ativo.",
                ],
                level="warning",
            )
            return

        pending_path = state.get("pending_path")
        offset = int(state.get("pending_offset", 0) or 0)
        lines = [line.strip() for line in raw_payload.splitlines() if line.strip()]
        line_count = len(lines)
        expected_total = int(current_file.get("registers", 0) or 0)
        next_offset = offset + line_count
        has_more = next_offset < expected_total if expected_total > 0 else False
        talhao = None
        total_saved = 0

        if lines:
            talhao, total_saved = append_tracker_package(
                file_path=pending_path,
                lines=lines,
                clear_existing=(offset == 0),
            )

        logger.info(
            "Pacote NDJSON processado. automation=%s path=%s offset=%s recebidas=%s salvas=%s talhao_id=%s has_more=%s",
            automation_config["name"],
            pending_path,
            offset,
            line_count,
            total_saved,
            getattr(talhao, "id", None),
            has_more,
        )

        state["pending_path"] = None

        if has_more:
            self.request_package(
                automation_config=automation_config,
                path=pending_path,
                offset=next_offset,
                limit=self.PACKAGE_LIMIT,
            )
            return

        state["current_file_index"] += 1
        logger.info(
            "Arquivo sincronizado. automation=%s path=%s proximo_indice=%s",
            automation_config["name"],
            pending_path,
            state["current_file_index"],
        )
        self.request_next_package(automation_config)

    def request_next_package(self, automation_config):
        current_file = self.get_current_file_state(automation_config)
        state = self.sync_state.get(automation_config["name"]) or {}

        if not current_file:
            completion_payload = {
                "type": "sync_broker_finished",
                "status": "success",
                "message": "Sincronizacao concluida",
                "total_files": len(state.get("files") or []),
            }
            logger.info(
                "Sincronizacao finalizada. automation=%s total_files=%s",
                automation_config["name"],
                len(state.get("files") or []),
            )
            
            # Isso aqui faz o uc excluir os arquivos temporarios e liberar recursos relacionados a sincronizacao
            #self.publish(completion_payload, automation_config["topic_broker_to_uc"])
            
            logger.info(
                "UC notificado sobre fim da sincronizacao. automation=%s topic=%s",
                automation_config["name"],
                automation_config["topic_broker_to_uc"],
            )
            return

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

        current_index = int(state.get("current_file_index", 0) or 0)
        files = state.get("files") or []
        if current_index < 0 or current_index >= len(files):
            return None

        return files[current_index]

    def request_package(self, automation_config, path, offset, limit):
        state = self.sync_state.setdefault(
            automation_config["name"],
            {
                "files": [],
                "current_file_index": 0,
                "pending_path": None,
                "pending_offset": 0,
                "pending_limit": self.PACKAGE_LIMIT,
            },
        )
        state["pending_path"] = path
        state["pending_offset"] = offset
        state["pending_limit"] = limit

        payload = {
            "type": "sync_broker_load_package",
            "path": path,
            "offset": offset,
            "limit": limit,
        }
        logger.info(
            "Solicitando pacote. automation=%s path=%s offset=%s limit=%s",
            automation_config["name"],
            path,
            offset,
            limit,
        )
        self.publish(payload, automation_config["topic_broker_to_uc"])

    def publish(self, payload, topic):
        message = json.dumps(payload, ensure_ascii=False)
        result = self.client.publish(topic, message)
        logger.info("Mensagem MQTT publicada. topic=%s mid=%s", topic, getattr(result, "mid", None))
