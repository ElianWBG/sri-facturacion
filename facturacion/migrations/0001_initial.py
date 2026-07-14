import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Contribuyente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_key', models.CharField(db_index=True, editable=False, max_length=64, unique=True)),
                ('nombre_referencia', models.CharField(help_text='Nombre interno para identificar al cliente del servicio', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('ruc', models.CharField(max_length=13)),
                ('razon_social', models.CharField(max_length=300)),
                ('nombre_comercial', models.CharField(blank=True, max_length=300)),
                ('dir_matriz', models.CharField(max_length=300)),
                ('dir_establecimiento', models.CharField(blank=True, help_text='Si está vacío se usa dir_matriz', max_length=300)),
                ('codigo_establecimiento', models.CharField(default='001', max_length=3)),
                ('punto_emision', models.CharField(default='001', max_length=3)),
                ('ambiente', models.CharField(choices=[('1', 'Pruebas'), ('2', 'Producción')], default='1', max_length=1)),
                ('obligado_contabilidad', models.BooleanField(default=False)),
                ('contribuyente_especial', models.CharField(blank=True, help_text='Vacío si no aplica', max_length=10)),
                ('firma_p12', models.FileField(blank=True, null=True, upload_to='firmas/')),
                ('clave_firma', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Contribuyente',
                'verbose_name_plural': 'Contribuyentes',
                'ordering': ['razon_social'],
            },
        ),
        migrations.CreateModel(
            name='SecuenciaFactura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('establecimiento', models.CharField(max_length=3)),
                ('punto_emision', models.CharField(max_length=3)),
                ('ultimo_numero', models.BigIntegerField(default=0)),
                ('contribuyente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='secuencias', to='facturacion.contribuyente')),
            ],
            options={
                'verbose_name': 'Secuencia de factura',
                'verbose_name_plural': 'Secuencias de facturas',
                'unique_together': {('contribuyente', 'establecimiento', 'punto_emision')},
            },
        ),
        migrations.CreateModel(
            name='Factura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('ENVIADO', 'Enviado'), ('AUTORIZADO', 'Autorizado'), ('RECHAZADO', 'Rechazado'), ('DEVUELTO', 'Devuelto')], db_index=True, default='PENDIENTE', max_length=12)),
                ('clave_acceso', models.CharField(blank=True, db_index=True, max_length=49, unique=True)),
                ('numero_autorizacion', models.CharField(blank=True, max_length=49)),
                ('fecha_autorizacion', models.DateTimeField(blank=True, null=True)),
                ('establecimiento', models.CharField(max_length=3)),
                ('punto_emision', models.CharField(max_length=3)),
                ('secuencial', models.CharField(max_length=9)),
                ('ambiente', models.CharField(default='1', max_length=1)),
                ('cliente_identificacion', models.CharField(max_length=20)),
                ('cliente_tipo_identificacion', models.CharField(default='05', max_length=2)),
                ('cliente_razon_social', models.CharField(max_length=300)),
                ('cliente_email', models.EmailField(blank=True, max_length=254)),
                ('cliente_direccion', models.CharField(blank=True, max_length=300)),
                ('cliente_telefono', models.CharField(blank=True, max_length=30)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('iva', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('payload', models.JSONField(default=dict)),
                ('xml_path', models.CharField(blank=True, max_length=500)),
                ('xml_autorizado_path', models.CharField(blank=True, max_length=500)),
                ('pdf_path', models.CharField(blank=True, max_length=500)),
                ('mensaje_sri', models.TextField(blank=True)),
                ('intentos', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contribuyente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='facturas', to='facturacion.contribuyente')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['estado', 'created_at'], name='fact_estado_created_idx'),
                    models.Index(fields=['contribuyente', 'estado'], name='fact_contrib_estado_idx'),
                ],
            },
        ),
    ]
