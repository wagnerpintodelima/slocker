import json
import logging
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from django.conf import settings

from backend.Controller.BaseController import doLog
from backend.models import TalhaoChild
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
        """Lê as configurações do MQTT e inicializa o cliente com seus callbacks."""
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
        """Retorna a lista de tópicos das automações configuradas."""
        return list(self.AUTOMATIONS_TOPICS)

    def describe_connect_rc(self, rc):
        """Traduz o código de retorno da conexão MQTT para uma descrição legível."""
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
        """Imprime e registra uma mensagem no log."""
        clean_message = str(message).rstrip()
        try:
            print(clean_message)
        except Exception:
            pass

        log_method = getattr(logger, level, logger.info)
        for line in clean_message.splitlines():
            log_method(line)

    def emit_block(self, title, lines, level="info"):
        """Monta e registra um bloco de log formatado."""
        block_lines = [
            "",
            "=" * 90,
            title,
            "-" * 90,
        ]
        block_lines.extend(str(line) for line in lines)
        block_lines.append("=" * 90)
        self.emit("\n".join(block_lines), level=level)

    def get_automation_uuid(self, automation_config=None, topic=None):
        """Extrai o identificador da automacao a partir do topico MQTT."""
        if automation_config and automation_config.get("name"):
            return str(automation_config["name"]).strip()

        raw_topic = str(topic or "").strip("/")
        if raw_topic:
            return raw_topic.split("/")[0]

        return "automacao-desconhecida"

    def log_system_event(self, title, message, level=2, automation_config=None, topic=None):
        """Registra um evento no log de sistema com identificacao da automacao."""
        automation_uuid = self.get_automation_uuid(automation_config=automation_config, topic=topic)
        doLog(
            title,
            f"<b>AUTO MESSAGE</b> - [{automation_uuid}] {message}",
            level,
        )

    def run_forever(self, reconnect_delay=5):
        """Mantém o listener rodando e tenta reconectar em caso de falha."""
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
        """Publica status online e se inscreve nos tópicos após conectar ao broker."""
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
            self.log_system_event(
                "MQTT automacao conectada",
                f"Automacao conectada ao broker e inscrita no topico <b>{item['topic_uc_to_broker']}</b>.",
                automation_config=item,
                topic=item["topic_uc_to_broker"],
            )

    def on_disconnect(self, client, userdata, rc):
        """Registra no log quando a conexão MQTT é encerrada."""
        logger.warning("MQTT desconectado. rc=%s", rc)

    def on_message(self, client, userdata, msg):
        """Decodifica a mensagem MQTT, converte o payload JSON e encaminha o tratamento."""
        raw_payload = msg.payload.decode("utf-8", errors="replace")
        automation_config = self.topic_map.get(msg.topic)

        if not automation_config:
            return

        data = self.parse_message_payload(raw_payload)
        if data is None:
            logger.warning(
                "Payload MQTT invalido. automation=%s topic=%s",
                automation_config["name"],
                msg.topic,
            )
            return
        self.handle_payload(data, automation_config)

    def parse_message_payload(self, raw_payload):
        """Aceita JSON comum, lista JSON ou NDJSON bruto vindo do UC."""
        if raw_payload is None:
            return None

        payload_text = str(raw_payload).strip()
        if not payload_text:
            return None

        try:
            return json.loads(payload_text)
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

        ndjson_items = []
        for line in payload_text.splitlines():
            normalized_line = line.strip().rstrip(",")
            if not normalized_line:
                continue
            try:
                ndjson_items.append(json.loads(normalized_line))
            except (TypeError, ValueError, json.JSONDecodeError):
                return None

        if not ndjson_items:
            return None

        return {
            "type": "sync_package",
            "path": None,
            "offset": 0,
            "count": len(ndjson_items),
            "has_more": False,
            "data": ndjson_items,
        }

    def handle_payload(self, data, automation_config):
        """Decide se o payload representa inventário, pacote de sincronização ou caso não tratado."""
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

    def is_sync_inventory_payload(self, data):
        """Identifica se o JSON representa um inventário de arquivos para sincronização."""
        return str(data.get("type", "")).strip().lower() == "sync_inventory" or isinstance(
            data.get("files"), list
        )

    def is_sync_package_payload(self, data):
        """Identifica se o JSON representa um pacote de dados de um arquivo."""
        return "path" in data and isinstance(self.get_sync_package_lines(data), list)

    def get_sync_package_lines(self, data):
        """Busca a lista de registros do pacote nas chaves aceitas do payload."""
        for key in ("data", "lines", "items", "records"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return []

    def handle_sync_inventory(self, data, automation_config):
        """Normaliza o inventário recebido, inicia o estado da sincronização e solicita o primeiro pacote."""
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
        """Processa um pacote recebido e decide se continua no arquivo atual ou avança para o próximo."""
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

        current_file = self.get_current_file_state(automation_config) or {}
        expected_total = int(current_file.get("registers", 0) or 0)
        package_lines = self.get_sync_package_lines(data)
        path = data.get("path") or state.get("pending_path")
        requested_offset = int(state.get("pending_offset", 0) or 0)
        response_offset = int(data.get("offset", requested_offset) or 0)
        offset = requested_offset
        count = int(data.get("count", len(package_lines)) or 0)
        has_more = data.get("has_more")

        if response_offset != requested_offset:
            logger.warning(
                "Offset divergente no pacote MQTT. automation=%s path=%s solicitado=%s recebido=%s",
                automation_config["name"],
                path,
                requested_offset,
                response_offset,
            )

        logger.info(
            "Pacote JSON recebido. automation=%s path=%s offset=%s count=%s has_more=%s",
            automation_config["name"],
            path,
            offset,
            count,
            has_more,
        )
        talhao, total_saved, talhao_created, previous_count, current_count = append_tracker_package(
            file_path=path,
            lines=package_lines,
            clear_existing=False,
        )
        if talhao_created:
            logger.info(
                "Talhao criado para sincronizacao. automation=%s path=%s talhao_id=%s talhao_nome=%s registros_adicionados=%s total_registros=%s",
                automation_config["name"],
                path,
                getattr(talhao, "id", None),
                getattr(talhao, "name", None),
                total_saved,
                current_count,
            )
            self.log_system_event(
                "MQTT talhao criado",
                f"Talhao <b>{getattr(talhao, 'name', '-')}</b> (#{getattr(talhao, 'id', '-')}) criado com <b>{total_saved}</b> elemento(s).",
                automation_config=automation_config,
                topic=automation_config["topic_uc_to_broker"],
            )
        else:
            logger.info(
                "Talhao existente atualizado. automation=%s path=%s talhao_id=%s talhao_nome=%s registros_anteriores=%s registros_adicionados=%s total_registros=%s",
                automation_config["name"],
                path,
                getattr(talhao, "id", None),
                getattr(talhao, "name", None),
                previous_count,
                total_saved,
                current_count,
            )
            self.log_system_event(
                "MQTT talhao atualizado",
                f"Talhao <b>{getattr(talhao, 'name', '-')}</b> (#{getattr(talhao, 'id', '-')}) atualizado com <b>{total_saved}</b> novo(s) elemento(s).",
                automation_config=automation_config,
                topic=automation_config["topic_uc_to_broker"],
            )

        state["pending_path"] = None

        if expected_total > 0:
            has_more = current_count < expected_total
        elif has_more is None:
            requested_limit = int(state.get("pending_limit", self.PACKAGE_LIMIT) or self.PACKAGE_LIMIT)
            has_more = count >= requested_limit and count > 0
        else:
            has_more = bool(has_more)

        logger.info(
            "Estado de continuidade do pacote. automation=%s path=%s total_atual=%s esperado=%s continuar=%s",
            automation_config["name"],
            path,
            current_count,
            expected_total,
            has_more,
        )

        if has_more:
            self.request_package(
                automation_config=automation_config,
                path=path,
                offset=current_count,
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

    def request_next_package(self, automation_config):
        """Solicita o primeiro pacote do arquivo atual ou encerra a sincronização quando não houver mais arquivos."""
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
            self.publish(completion_payload, automation_config["topic_broker_to_uc"])
            
            logger.info(
                "UC notificado sobre fim da sincronizacao. automation=%s topic=%s",
                automation_config["name"],
                automation_config["topic_broker_to_uc"],
            )
            return

        existing_count = self.get_saved_register_count(current_file["path"])
        expected_total = int(current_file.get("registers", 0) or 0)

        if expected_total > 0 and existing_count >= expected_total:
            logger.info(
                "Arquivo ja sincronizado. automation=%s path=%s salvos=%s esperados=%s",
                automation_config["name"],
                current_file["path"],
                existing_count,
                expected_total,
            )
            self.log_system_event(
                "MQTT arquivo ja sincronizado",
                f"Talhao <b>{Path(current_file['path']).name}</b> ja estava atualizado. Elementos no broker: <b>{existing_count}</b>.",
                automation_config=automation_config,
                topic=automation_config["topic_uc_to_broker"],
            )
            state["current_file_index"] += 1
            self.request_next_package(automation_config)
            return

        self.request_package(
            automation_config=automation_config,
            path=current_file["path"],
            offset=existing_count,
            limit=self.PACKAGE_LIMIT,
        )

    def get_current_file_state(self, automation_config):
        """Retorna o arquivo atualmente apontado pelo estado da sincronização."""
        state = self.sync_state.get(automation_config["name"])
        if not state:
            return None

        current_index = int(state.get("current_file_index", 0) or 0)
        files = state.get("files") or []
        if current_index < 0 or current_index >= len(files):
            return None

        return files[current_index]

    def get_saved_register_count(self, path):
        """Retorna quantos registros ja foram salvos para o talhao associado ao nome do arquivo."""
        talhao_name = Path(path).name
        talhao = (
            TalhaoChild.objects.filter(talhao__name=talhao_name)
            .order_by("-talhao__created_at", "-talhao__id")
            .values_list("talhao_id", flat=True)
            .first()
        )
        if not talhao:
            return 0
        return TalhaoChild.objects.filter(talhao_id=talhao).count()

    def request_package(self, automation_config, path, offset, limit):
        """Atualiza o estado do pacote pendente e publica a solicitação via MQTT."""
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
        """Serializa o payload em JSON e publica a mensagem no tópico MQTT informado."""
        message = json.dumps(payload, ensure_ascii=False)
        result = self.client.publish(topic, message)
        logger.info("Mensagem MQTT publicada. topic=%s mid=%s", topic, getattr(result, "mid", None))
