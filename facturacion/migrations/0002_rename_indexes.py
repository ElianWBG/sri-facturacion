from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='factura',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='factura',
            name='clave_acceso',
            field=models.CharField(blank=True, db_index=True, max_length=49, unique=True),
        ),
        migrations.RenameIndex(
            model_name='factura',
            new_name='facturacion_estado_88fc09_idx',
            old_name='fact_estado_created_idx',
        ),
        migrations.RenameIndex(
            model_name='factura',
            new_name='facturacion_contrib_9cade6_idx',
            old_name='fact_contrib_estado_idx',
        ),
    ]
