# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from django.db import models
from django.contrib.auth.models import User


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'



class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)



class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'

class Client(models.Model):
    razao_social = models.CharField(max_length=50)
    nome_fantasia = models.CharField(max_length=50)
    email = models.CharField(max_length=255)
    cpf_cnpj = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    cep = models.CharField(max_length=15)
    uf_description = models.CharField(max_length=50)
    uf = models.CharField(max_length=2)
    city = models.CharField(max_length=50)
    neighborhood = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    house_number = models.CharField(max_length=10)
    observation = models.CharField(max_length=32)
    picture = models.CharField(max_length=255)
    logo = models.CharField(max_length=255)
    is_main = models.BooleanField()
    status = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'client'


class UserAppAddress(models.Model):
    title = models.CharField(max_length=20)
    cep = models.CharField(max_length=15)
    uf_description = models.CharField(max_length=50)
    uf = models.CharField(max_length=2)
    city = models.CharField(max_length=50)
    neighborhood = models.CharField(max_length=50)
    street = models.CharField(max_length=50)
    house_number = models.CharField(max_length=10)
    observation = models.CharField(max_length=100)
    status = models.BooleanField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'user_app_address'


class UserApp(models.Model):
    client = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True)
    user_app_address = models.ForeignKey('UserAppAddress', models.DO_NOTHING, blank=True, null=True)    
    hu = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=50)
    signature = models.CharField(max_length=255)
    password = models.TextField()
    cpf = models.CharField(max_length=15)
    phone_number = models.CharField(max_length=17)
    picture = models.CharField(max_length=255)
    api_facebook = models.BooleanField()
    user_id_facebook = models.CharField(max_length=512)
    api_google = models.BooleanField()
    sub_user_google = models.CharField(max_length=512)
    token_fcm = models.CharField(max_length=512)
    so = models.CharField(max_length=50)
    is_doorman = models.BooleanField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()
    status = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'user_app'

class AutomationType(models.Model):
    description = models.CharField(max_length=50)
    route = models.CharField(max_length=255) # Rota para quando ser clicado
    status = models.BooleanField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'automation_type'

class Automation(models.Model):
    client = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True)
    cliente_auten = models.ForeignKey('ClienteAuten', models.DO_NOTHING, blank=True, null=True, db_column='cliente_auten')
    automation_type = models.ForeignKey('AutomationType', models.DO_NOTHING, blank=True, null=True)
    ip = models.CharField(max_length=50)
    subnet = models.CharField(max_length=50)
    gateway = models.CharField(max_length=50)
    mac = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=15)
    description = models.TextField()
    type_location = models.CharField(max_length=50)
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'automation'

class UserSystem(models.Model):
    client = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True)
    auth_user = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True)
    picture = models.CharField(max_length=255)
    observation = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'user_system'

class HU(models.Model):
    automation = models.ForeignKey('Automation', models.DO_NOTHING, blank=True, null=True)    
    hu_id = models.IntegerField()
    apartamento = models.CharField(max_length=5)    
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'hu'

class Keyword(models.Model):
    client = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True)    
    hu = models.CharField(max_length=10)
    word = models.CharField(max_length=100)    
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'keyword'

class Locacao(models.Model):    
    locacao_id = models.IntegerField() # Isso é o ID da locação lá no sqlite da rasp
    client = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True)    
    slot = models.CharField(max_length=10)
    hu = models.CharField(max_length=10)
    keyword = models.CharField(max_length=50)
    password = models.CharField(max_length=10)            
    delivered_at = models.DateTimeField()    
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'locacao'

class Slot(models.Model):
    automation = models.ForeignKey('Automation', models.DO_NOTHING, blank=True, null=True)    
    slot_id = models.IntegerField() # Isso é o ID do slot lá no sqlite da rasp
    description = models.CharField(max_length=10)
    name = models.CharField(max_length=10)    
    model = models.CharField(max_length=15)    
    status = models.IntegerField() # 0: closed, 1: wait_to_open,	2: wait_to_close,	3: receiver_authorized, 4: open_not_authorized,	5: canceled
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'slot'
        
class AtronUpdate(models.Model):        
    version_current = models.CharField(max_length=30)
    description = models.CharField(max_length=255)    
    apk = models.CharField(max_length=255)        
    level = models.IntegerField() #0: Normal, 1: Urgente e 2: Forced
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'atron_update'
        
class AtronDeviceRegister(models.Model):        
    device_number = models.CharField(max_length=255)    
    version_current = models.CharField(max_length=30)
    lat = models.CharField(max_length=128)        
    lon = models.CharField(max_length=128)        
    satellites = models.IntegerField()
    timestamp_in_gps = models.DateTimeField()
    status = models.IntegerField() # 0: Já foi usado, 1: Disponível
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'atron_device_register'        


class AtronDevice(models.Model):   
    automation = models.ForeignKey('Automation', models.DO_NOTHING, blank=True, null=True)     
    atron_device_register = models.ForeignKey('AtronDeviceRegister', models.DO_NOTHING, blank=True, null=True)     
    version_current = models.CharField(max_length=30)
    description = models.TextField()
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'atron_device'           
        
        
class LogGate(models.Model):        
    client = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True)    
    condomino = models.CharField(max_length=10)    
    hu = models.CharField(max_length=30)    
    comando = models.CharField(max_length=50)    
    created_at = models.DateTimeField()    

    class Meta:
        managed = False
        db_table = 'log_gate'        

class ClienteAuten(models.Model):    
    nome = models.CharField(max_length=50)    
    cpf_cnpj = models.CharField(max_length=20)
    telefone = models.CharField(max_length=20)
    cep = models.CharField(max_length=15)    
    uf = models.CharField(max_length=20)
    cidade = models.CharField(max_length=50)
    endereco = models.CharField(max_length=100)    
    numero = models.CharField(max_length=10)
    observacao_endereco = models.TextField()
    link_gps = models.TextField()    
    status = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cliente_auten'
        
        
class Carro(models.Model):    
    empresa = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True, db_column='empresa')
    modelo = models.CharField(max_length=50)    
    marca = models.CharField(max_length=50)
    placa = models.CharField(max_length=20)
    ano = models.CharField(max_length=10)    
    cor = models.CharField(max_length=20)
    km_proxima_troca_oleo = models.IntegerField()
    km_proxima_troca_pneu = models.IntegerField()
    km_rodados = models.IntegerField()
    media_por_litro = models.CharField(max_length=32, null=True)
    foto = models.TextField()
    observacao = models.TextField()    
    status = models.BooleanField()    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True, auto_now=True)
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'carro'
        
        
class V2(models.Model):   
    automation = models.ForeignKey('Automation', models.DO_NOTHING, blank=True, null=True)         
    version_current = models.CharField(max_length=30)
    description = models.TextField()
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'v2'                   
        
class Tela(models.Model):   
    automation = models.ForeignKey('Automation', models.DO_NOTHING, blank=True, null=True)         
    version_current = models.CharField(max_length=30)
    description = models.TextField()
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tela'            
        
class Sensor(models.Model):   
    automation = models.ForeignKey('Automation', models.DO_NOTHING, blank=True, null=True)         
    version_current = models.CharField(max_length=30)
    modelo = models.CharField(max_length=30)
    description = models.TextField()
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'sensor'     
        
class Tecnico(models.Model):   
    empresa = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True, db_column='empresa')         
    user_auth = models.ForeignKey('AuthUser', models.DO_NOTHING, blank=True, null=True, db_column='user_auth')         
    nome = models.CharField(max_length=50)
    telefone = models.CharField(max_length=20)
    foto = models.CharField(max_length=255)
    viagens_realizadas = models.IntegerField()
    km_rodados = models.IntegerField()
    observacao = models.CharField(max_length=255)
    status = models.BooleanField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tecnico'                    
        
        
STATUS_CHOICES = [
    (0, "Agendado"),
    (1, "Atrasado"),
    (2, "Em viagem"),
    (3, "Acerto finalizado"),
    (4, "Acerto pendente"),    
]        
class Viagem(models.Model):   
    empresa = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True, db_column='empresa')
    cliente_auten = models.ForeignKey('ClienteAuten', models.DO_NOTHING, blank=True, null=True, db_column='cliente_auten')
    tecnico = models.ForeignKey('Tecnico', models.DO_NOTHING, blank=True, null=True, db_column='tecnico')
    carro = models.ForeignKey('Carro', models.DO_NOTHING, blank=True, null=True, db_column='carro')
    km_saida = models.IntegerField()
    km_chegada = models.IntegerField()
    km_previsto = models.IntegerField()
    data_saida = models.DateTimeField()
    data_chegada = models.DateTimeField()
    data_chegada_prevista = models.DateTimeField()
    data_saida_prevista = models.DateTimeField()
    link_gps = models.TextField()
    observacao = models.CharField(max_length=255)
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'viagem'

MAQUINA_TIPO_CHOICES = [
    (0, 'Autopropelido'),
    (1, 'Arrastão'),
    (2, 'Hidráulico'),
    (3, 'Trator')
]

MAQUINA_TIPO_PULSO_CHOICES = [
    (0, 'Pulso Postivo'),
    (1, 'Pulso Negativo'),
    (2, 'É personalizado, está descrito nas observações')
]
class Maquina(models.Model):           
    modelo = models.CharField(max_length=50)    
    tipo = models.IntegerField(choices=MAQUINA_TIPO_CHOICES, default=0)
    tipo_pulso = models.IntegerField(choices=MAQUINA_TIPO_PULSO_CHOICES, default=0)
    usa_rele = models.BooleanField(null=True)
    foto = models.CharField(max_length=255)    
    observacao = models.TextField()
    status = models.BooleanField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maquina'

MAQUINA_MODELO_CHOICES = [
    # --- AUTOPROPELIDOS ---
    (0, "Stara 3000"),
    (1, "Stara 4000"),
    (2, "Stara Imperador 3.0"),
    (3, "Stara Imperador 3000"),
    (4, "Stara Imperador 4000"),
    (5, "Stara Gladiador 3000"),
    (6, "Jacto 2530"),
    (7, "Jacto 3030"),
    (8, "Jacto 4530"),
    (9, "Jacto Advance 2000"),
    (10, "Jacto Advance 3000"),
    (11, "Jacto Uniporte 2030"),
    (12, "Jacto Uniporte 2530"),
    (13, "Jacto Uniporte 3030"),
    (14, "Jacto Uniporte 4530"),
    (15, "Jacto Columbia AD18 21m"),
    (16, "John Deere M4030"),
    (17, "John Deere M4040"),
    (18, "John Deere M4045"),
    (19, "John Deere R4030"),
    (20, "Case IH Patriot 250"),
    (21, "Case IH Patriot 350"),
    (22, "Case IH Patriot 400"),
    (23, "Case IH Patriot 250 Extreme"),
    (24, "New Holland SP350F"),
    (25, "New Holland SP370F"),
    (26, "New Holland SP410F"),
    (27, "Kuhn Stronger HD"),
    (28, "Kuhn Stronger 4000"),
    (29, "PLA MAP II 3000"),
    (30, "PLA MAP III 3250"),

    # --- DE ARRASTO (REBOCADOS) ---
    (31, "Jacto Advance 2000 AM18"),
    (32, "Jacto Condor 800"),
    (33, "Jacto Condor 1200"),
    (34, "Jacto Condor 2000"),
    (35, "Stara Hercules 2000"),
    (36, "Stara Hercules 3000"),
    (37, "Kuhn Montana Hercules 3000"),
    (38, "John Deere 4630 Trailed"),
    (39, "Jan Tornado 600"),
    (40, "Jan Tornado 1200"),
    (41, "KF Agrícola Master 2000"),
    (42, "Kuhn Columbia 2000"),

    # --- HIDRÁULICOS (3 PONTOS) ---
    (43, "Jacto PJH"),
    (44, "Jacto Advance 400"),
    (45, "Jacto Arbus 400"),
    (46, "Kuhn PF 1000"),
    (47, "Stara Pulverizador Acoplado Hercules 800"),
    (48, "Stara Hercules 600"),
    (49, "Jan Hercules 600"),
    (50, "PLA Trail 1000"),
    (51, "KF Agrícola Master 600"),
    (52, "Jacto Condor 600 AM14"),
]

TIPO_INSTALACAO_CHOICES = [
    (0, "Vic Sensor"),
    (1, "GPS Atron"),
    (2, "GPS Tablet"),
    (3, "kit Ponta"),
    (4, "Kit Luz"),
    (5, "Kit Barra + Água")
]

class ViagemInstalacao(models.Model):   
    viagem_instalacao_pai = models.ForeignKey('ViagemInstalacao', models.DO_NOTHING, blank=True, null=True, db_column='viagem_instalacao_pai')
    maquina = models.ForeignKey('Maquina', models.DO_NOTHING, blank=False, null=False, db_column='maquina')
    viagem = models.ForeignKey('Viagem', models.DO_NOTHING, blank=True, null=True, db_column='viagem')
    cliente_auten = models.ForeignKey('ClienteAuten', models.DO_NOTHING, blank=True, null=True, db_column='cliente')
    tipo_instalacao = models.IntegerField(choices=TIPO_INSTALACAO_CHOICES, default=0)
    maquina_modelo = models.IntegerField(choices=MAQUINA_MODELO_CHOICES, default=0) # Não usamos mais
    foto_capa = models.CharField(max_length=255)    
    job = models.TextField() # Serviço à ser feito
    descricao_atendimento = models.TextField()
    status = models.BooleanField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'viagem_instalacao'        
        
        
SATISFACAO = [
    (0, "Muito Insatisfeito"),
    (1, "Insatisfeito"),
    (2, "Neutro"),
    (3, "Satisfeiro"),
    (4, "Muito Satisfeito")    
]        
class PosVenda(models.Model):   
    viagem_instalacao = models.ForeignKey('ViagemInstalacao', models.DO_NOTHING, blank=True, null=True, db_column='viagem_instalacao')
    descricao = models.TextField()        
    satisfacao_cliente = models.IntegerField(choices=SATISFACAO, default=2)
    data_programada_ligacao = models.DateTimeField()
    status = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'pos_venda'
        
MODO_OPERACAO_CHOICES = [
    (0, 'Independente'),
    (1, 'Concorrente'),
]
     
class V2Configuracao(models.Model):   
    
    v2 = models.ForeignKey('V2', models.DO_NOTHING, blank=True, null=True, db_column='v2')
    
    # Geral
    modo_padrao = models.IntegerField()
    altura_barra = models.IntegerField()
    altura_quadro = models.IntegerField()
    modo_operacao = models.IntegerField(choices=MODO_OPERACAO_CHOICES, default=0)
    modo_operacao_zc = models.IntegerField(choices=MODO_OPERACAO_CHOICES, default=0)
    subir_direto_interno = models.IntegerField()
    subir_direto_externo = models.IntegerField()
    tempo_espera_zc = models.IntegerField()
    planar = models.BooleanField()
    compensar_altura_porcentagem = models.IntegerField()
    pitch_min = models.IntegerField()
    pitch_max = models.IntegerField()
    roll_min = models.IntegerField()
    roll_max = models.IntegerField()
    yaw = models.IntegerField()
    amostras_interno = models.IntegerField()
    amostras_externo = models.IntegerField()
    sensor_interno_habilitado = models.BooleanField()
    
    # Configurações da Barra Direita
    t_subida_direita = models.IntegerField()
    t_descida_direita = models.IntegerField()
    duty_subida_min_direita = models.IntegerField()
    duty_subida_max_direita = models.IntegerField()
    duty_descida_min_direita = models.IntegerField()
    duty_descida_max_direita = models.IntegerField()
    compensar_negativo_habilitado_direita = models.BooleanField()
    compensar_positivo_habilitado_direita = models.BooleanField()
    compensar_negativo_direita = models.IntegerField()
    compensar_positivo_direita = models.IntegerField()
    margem_superior_ext_one_direita = models.IntegerField()
    margem_inferior_ext_one_direita = models.IntegerField()
    margem_inferior_int_one_direita = models.IntegerField()
    tempo_espera_one_direita = models.IntegerField()
    margem_superior_ext_two_direita = models.IntegerField()
    margem_inferior_ext_two_direita = models.IntegerField()          
    margem_inferior_int_two_direita = models.IntegerField()
    tempo_espera_two_direita = models.IntegerField()
    margem_superior_ext_three_direita = models.IntegerField()
    margem_inferior_ext_three_direita = models.IntegerField()
    margem_inferior_int_three_direita = models.IntegerField()
    tempo_espera_three_direita = models.IntegerField()
    
    # Configurações da Barra Esquerda
    t_subida_esquerda = models.IntegerField()
    t_descida_esquerda = models.IntegerField()
    duty_subida_min_esquerda = models.IntegerField()
    duty_subida_max_esquerda = models.IntegerField()
    duty_descida_min_esquerda = models.IntegerField()
    duty_descida_max_esquerda = models.IntegerField()
    compensar_negativo_habilitado_esquerda = models.BooleanField()
    compensar_positivo_habilitado_esquerda = models.BooleanField()
    compensar_negativo_esquerda = models.IntegerField()
    compensar_positivo_esquerda = models.IntegerField()
    margem_superior_ext_one_esquerda = models.IntegerField()
    margem_inferior_ext_one_esquerda = models.IntegerField()
    margem_inferior_int_one_esquerda = models.IntegerField()
    tempo_espera_one_esquerda = models.IntegerField()
    margem_superior_ext_two_esquerda = models.IntegerField()
    margem_inferior_ext_two_esquerda = models.IntegerField()          
    margem_inferior_int_two_esquerda = models.IntegerField()
    tempo_espera_two_esquerda = models.IntegerField()
    margem_superior_ext_three_esquerda = models.IntegerField()
    margem_inferior_ext_three_esquerda = models.IntegerField()
    margem_inferior_int_three_esquerda = models.IntegerField()
    tempo_espera_three_esquerda = models.IntegerField()  
    
    # Configurações da Barra Quadro
    t_subida_quadro = models.IntegerField()
    t_descida_quadro = models.IntegerField()
    duty_subida_min_quadro = models.IntegerField()
    duty_subida_max_quadro = models.IntegerField()
    duty_descida_min_quadro = models.IntegerField()
    duty_descida_max_quadro = models.IntegerField()
    compensar_negativo_habilitado_quadro = models.BooleanField()
    compensar_positivo_habilitado_quadro = models.BooleanField()
    compensar_negativo_quadro = models.IntegerField()
    compensar_positivo_quadro = models.IntegerField()
    margem_superior_ext_one_quadro = models.IntegerField()
    margem_inferior_ext_one_quadro = models.IntegerField()
    margem_inferior_int_one_quadro = models.IntegerField()
    tempo_espera_one_quadro = models.IntegerField()
    margem_superior_ext_two_quadro = models.IntegerField()
    margem_inferior_ext_two_quadro = models.IntegerField()          
    margem_inferior_int_two_quadro = models.IntegerField()
    tempo_espera_two_quadro = models.IntegerField()
    margem_superior_ext_three_quadro = models.IntegerField()
    margem_inferior_ext_three_quadro = models.IntegerField()
    margem_inferior_int_three_quadro = models.IntegerField()
    tempo_espera_three_quadro = models.IntegerField()     
    
    # Default
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'v2_configuracao'        
        
        
class ViagemInstalacaoKit(models.Model):   
    viagem_instalacao = models.ForeignKey('ViagemInstalacao', models.DO_NOTHING, blank=True, null=True, db_column='viagem_instalacao')
    descricao = models.TextField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'viagem_instalacao_kit'
        
        
STATUS_KIT_CHOICES = [
    (0, 'Pendente'),
    (1, 'Devolvido'),
    (2, 'Vendido'),
    (3, 'Danificado'),
]
class ViagemInstalacaoKitChild(models.Model):   
    viagem_instalacao_kit = models.ForeignKey('ViagemInstalacaoKit', models.DO_NOTHING, blank=True, null=True, db_column='viagem_instalacao_kit')
    v2 = models.ForeignKey('V2', models.DO_NOTHING, blank=True, null=True, db_column='v2')
    sensor = models.ForeignKey('Sensor', models.DO_NOTHING, blank=True, null=True, db_column='sensor')
    tela = models.ForeignKey('Tela', models.DO_NOTHING, blank=True, null=True, db_column='tela')    
    outro = models.TextField()
    is_reserva = models.BooleanField()
    status = models.IntegerField(choices=STATUS_KIT_CHOICES, default=0)
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'viagem_instalacao_kit_child'        
                        
STATUS_LEVEL_CHOICES = [
    (0, 'ERROR'),
    (1, 'SUCCESS'),
    (2, 'WARNING'),
    (3, 'INFO')
]
class Log(models.Model):           
    titulo = models.CharField(max_length=30)
    descricao = models.CharField(max_length=255)
    level = models.IntegerField(choices=STATUS_LEVEL_CHOICES, default=0)
    created_at = models.DateTimeField()    

    class Meta:
        managed = False
        db_table = 'log'                
        
STATUS_CALL_CHOICES = [
    (0, 'Pendente'),
    (1, 'Resolvido'),
    (2, 'Atrasado'),
    (3, 'Em atendimento')
]        

PRIORIDADE_CALL_CHOICES = [
    (0, 'Normal'),
    (1, 'Urgente'),
    (2, 'Imediatamente')
]      

ASSUNTO_CALL_CHOICES = [
    (0, 'V2'),
    (1, 'GPS'),
    (3, 'Sensor'),
    (4, 'Kit Barra + Água'),
    (5, 'Kit Luz'),
    (6, 'Kit Câmera')
]      
class Call(models.Model):           
    cliente_auten = models.ForeignKey('ClienteAuten', models.DO_NOTHING, blank=True, null=True, db_column='cliente_auten')
    tecnico = models.ForeignKey('Tecnico', models.DO_NOTHING, blank=True, null=True, db_column='tecnico')
    assunto = models.IntegerField(choices=ASSUNTO_CALL_CHOICES, default=0)
    descricao = models.TextField()
    resposta = models.TextField()
    prioridade = models.IntegerField(choices=PRIORIDADE_CALL_CHOICES, default=0)
    call_at = models.DateTimeField()    
    status = models.IntegerField(choices=STATUS_CALL_CHOICES, default=0)
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'call'           
                
class CallChild(models.Model):           
    call = models.ForeignKey('Call', models.DO_NOTHING, blank=True, null=True, db_column='call')   
    resposta = models.TextField()
    next_action = models.TextField()    
    call_at = models.DateTimeField()        
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'call_child'         
                
class Produto(models.Model):
    codigo = models.CharField(max_length=50)
    empresa = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True, db_column='empresa')
    descricao = models.CharField(max_length=255)
    foto = models.TextField()
    quantidade_em_estoque = models.IntegerField(default=0)
    quantidade_minima = models.IntegerField(default=10)
    endereco = models.CharField(max_length=25)
    link = models.TextField()
    is_final = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'produto'                 
        
TIPO_MOV_ESTOQUE_CHOICES = [
    ('saida', 'Saída'),
    ('entrada', 'Entrada'),
    ('ajuste_estoque', 'Ajuste de Estoque')    
]        
class MovimentoEstoque(models.Model):           
    produto = models.ForeignKey('Produto', models.DO_NOTHING, blank=True, null=True, db_column='produto')   
    empresa = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True, db_column='empresa')       
    tipo = models.CharField(max_length=20, choices=TIPO_MOV_ESTOQUE_CHOICES)
    quantidade = models.IntegerField(default=1)
    descricao = models.TextField()
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    created_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'movimento_estoque'         
        
class ProdutoComposto(models.Model):
    empresa = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True, db_column='empresa')    
    produto_pai = models.ForeignKey('Produto', models.DO_NOTHING, blank=True, null=True, db_column='produto_pai')
    quantidade_elementos = models.IntegerField(default=1)
    diagrama = models.TextField(null=True, blank=True)
    gerber = models.TextField(null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()
    status = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'produto_composto'        

class ProdutoCompostoChild(models.Model):
    produto_composto = models.ForeignKey('ProdutoComposto', models.DO_NOTHING, blank=True, null=True, db_column='produto_composto')
    produto = models.ForeignKey('Produto', models.DO_NOTHING, blank=True, null=True, db_column='produto')
    quantidade = models.FloatField(default=1)
    observacao = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'produto_composto_child'       

CHOICE_STATUS_OP = [
    ('separacao', 'Separação'),
    ('producao_pendente', 'Aguardando Início Produção'),
    ('start', 'Produção em Andamento'),
    ('pause', 'Produção Pausada'),
    ('done', 'Produção Finalizada')
]
class OrdemProducao(models.Model):
    empresa = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True, db_column='empresa')    
    job = models.TextField()
    anexo = models.TextField()
    data_inicio  = models.DateTimeField()
    data_entrega = models.DateTimeField()
    status = models.CharField(choices=CHOICE_STATUS_OP, max_length=100, default='separacao')
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'ordem_producao'

class OrdemProducaoChild(models.Model):
    ordem_producao = models.ForeignKey('OrdemProducao', models.DO_NOTHING, blank=True, null=True, db_column='ordem_producao')
    produto = models.ForeignKey('Produto', models.DO_NOTHING, blank=True, null=True, db_column='produto')
    movimento_estoque = models.ForeignKey('MovimentoEstoque', models.DO_NOTHING, blank=True, null=True, db_column='movimento_estoque')
    quantidade  = models.IntegerField()
    observacao = models.TextField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()    

    class Meta:
        managed = False
        db_table = 'ordem_producao_child'        


class AlarmBarGroup(models.Model):    
    automation = models.ForeignKey('Automation', models.DO_NOTHING, blank=True, null=False, db_column='automation')    
    descricao = models.CharField(max_length=40, null=False)

    class Meta:
        managed = False
        db_table = 'alarm_bar_group'              
        
        
class AlarmBarGroupItem(models.Model):    
    alarm_bar_group = models.ForeignKey('AlarmBarGroup', models.DO_NOTHING, blank=True, null=False, db_column='alarm_bar_group')        
    descricao = models.CharField(max_length=40, null=False)

    class Meta:
        managed = False
        db_table = 'alarm_bar_group_item'
        
class AlarmBar(models.Model):
    automation = models.ForeignKey('Automation', models.DO_NOTHING, blank=True, null=True, db_column='automation')    
    alarm_bar_group_item = models.ForeignKey('AlarmBarGroupItem', models.DO_NOTHING, blank=True, null=False, db_column='alarm_bar_group_item')    
    wifi_ssid = models.CharField(max_length=100)
    wifi_pswd = models.CharField(max_length=100)
    wifi_ssid_local = models.CharField(max_length=100)
    wifi_pswd_local = models.CharField(max_length=100, default='12345678')
    mqtt_topic_uc_to_broker = models.CharField(max_length=255, default='alarm/bar/uc/send')
    mqtt_topic_broker_to_uc = models.CharField(max_length=255, default='alarm/bar/uc/receiver')
    imu_task_ms = models.IntegerField()
    min_pitch = models.IntegerField()
    max_pitch = models.IntegerField()
    min_roll = models.IntegerField()
    max_roll = models.IntegerField()
    max_pitch = models.IntegerField()
    min_yaw = models.IntegerField()
    max_yaw = models.IntegerField()
    tempo_disparo_seg = models.IntegerField(default=5)
    imu_active = models.BooleanField()
    status = models.BooleanField()
    created_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'alarm_bar'

class AlarmBarDisparo(models.Model):
    alarm_bar = models.ForeignKey('AlarmBar', models.DO_NOTHING, blank=True, null=True, db_column='alarm_bar')        
    pitch = models.IntegerField()
    roll = models.IntegerField()
    yaw = models.IntegerField()    
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'alarm_bar_disparo'        
        
        
