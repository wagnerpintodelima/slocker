# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from django.db import models
from django.contrib.auth.models import User


# Isso é uma View no banco de dados
class SaldoEstoque(models.Model):
    produto_id = models.IntegerField()
    descricao = models.CharField(max_length=255)
    empresa = models.ForeignKey('Client', models.DO_NOTHING, db_column='empresa')
    saldo_atual = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'saldo_estoque'        
        

class ItemReserva(models.Model):
    id = models.IntegerField(primary_key=True)
    descricao = models.CharField(max_length=50)
    tecnico = models.CharField(max_length=100)
    cliente = models.CharField(max_length=100)
    data_saida = models.DateTimeField()
    data_chegada_prevista = models.DateTimeField()

    class Meta:
        managed = False  # Importante! Não deixa o Django tentar criar/tocar essa tabela
        db_table = 'itens_reserva'
