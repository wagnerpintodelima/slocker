from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TrackerImportJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_path", models.CharField(max_length=255)),
                ("original_name", models.CharField(max_length=255)),
                ("talhao_id", models.BigIntegerField(db_index=True)),
                ("status", models.CharField(choices=[("pending", "Pendente"), ("processing", "Processando"), ("done", "Concluido"), ("error", "Erro")], default="pending", max_length=20)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("total_saved", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True, default="")),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "tracker_import_job",
            },
        ),
    ]
