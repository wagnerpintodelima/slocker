from django.core.management.base import BaseCommand

from backend.services.mqtt_listener import MqttListenerService


class Command(BaseCommand):
    help = "Inicia o listener MQTT principal da aplicacao."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reconnect-delay",
            type=int,
            default=5,
            help="Intervalo, em segundos, antes de tentar reconectar ao broker.",
        )

    def handle(self, *args, **options):
        reconnect_delay = max(options["reconnect_delay"], 1)
        self.stdout.write(self.style.SUCCESS("Iniciando listener MQTT principal."))
        service = MqttListenerService()
        service.run_forever(reconnect_delay=reconnect_delay)
