import secrets

from django.db import models


class Contribuyente(models.Model):
    """Negocio/empresa que usa el servicio. Cada uno tiene su propio
    RUC, firma electrónica, secuenciales y ambiente SRI completamente aislados."""

    # Autenticación
    api_key = models.CharField(max_length=64, unique=True, editable=False, db_index=True)
    nombre_referencia = models.CharField(max_length=100, help_text='Nombre interno para identificar al cliente del servicio')
    is_active = models.BooleanField(default=True)

    # Identidad tributaria
    ruc                     = models.CharField(max_length=13)
    razon_social            = models.CharField(max_length=300)
    nombre_comercial        = models.CharField(max_length=300, blank=True)
    dir_matriz              = models.CharField(max_length=300)
    dir_establecimiento     = models.CharField(max_length=300, blank=True, help_text='Si está vacío se usa dir_matriz')
    codigo_establecimiento  = models.CharField(max_length=3, default='001')
    punto_emision           = models.CharField(max_length=3, default='001')

    # Configuración SRI
    ambiente                = models.CharField(max_length=1, choices=[('1', 'Pruebas'), ('2', 'Producción')], default='1')
    obligado_contabilidad   = models.BooleanField(default=False)
    contribuyente_especial  = models.CharField(max_length=10, blank=True, help_text='Vacío si no aplica')

    # Firma electrónica (.p12)
    firma_p12               = models.FileField(upload_to='firmas/', blank=True, null=True)
    clave_firma             = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Contribuyente'
        verbose_name_plural = 'Contribuyentes'
        ordering = ['razon_social']

    def __str__(self):
        return f'{self.razon_social} ({self.ruc})'

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    is_authenticated = True  # requerido por DRF IsAuthenticated cuando se usa como request.user

    @property
    def simulado(self):
        """True cuando no hay firma real cargada. El flujo usa firma mock."""
        return not bool(self.firma_p12 and self.clave_firma)

    def as_emisor_dict(self) -> dict:
        """Devuelve el dict que esperan xml_builder y ride."""
        return {
            'RUC':                  self.ruc,
            'RAZON_SOCIAL':         self.razon_social,
            'NOMBRE_COMERCIAL':     self.nombre_comercial or self.razon_social,
            'DIR_MATRIZ':           self.dir_matriz,
            'DIR_ESTABLECIMIENTO':  self.dir_establecimiento or self.dir_matriz,
            'ESTABLECIMIENTO':      self.codigo_establecimiento,
            'PUNTO_EMISION':        self.punto_emision,
            'CONTRIBUYENTE_ESPECIAL': self.contribuyente_especial,
            'OBLIGADO_CONTABILIDAD': 'SI' if self.obligado_contabilidad else 'NO',
        }


class SecuenciaFactura(models.Model):
    """Contador atómico de secuenciales, por contribuyente + establecimiento + punto de emisión.
    Evita colisiones en entornos con múltiples workers Celery."""

    contribuyente   = models.ForeignKey(Contribuyente, on_delete=models.CASCADE, related_name='secuencias')
    establecimiento = models.CharField(max_length=3)
    punto_emision   = models.CharField(max_length=3)
    ultimo_numero   = models.BigIntegerField(default=0)

    class Meta:
        unique_together = [('contribuyente', 'establecimiento', 'punto_emision')]
        verbose_name = 'Secuencia de factura'
        verbose_name_plural = 'Secuencias de facturas'

    def __str__(self):
        return f'{self.contribuyente.ruc} · {self.establecimiento}-{self.punto_emision} → {self.ultimo_numero}'


class Factura(models.Model):
    """Comprobante electrónico y su ciclo de vida."""

    class Estado(models.TextChoices):
        PENDIENTE  = 'PENDIENTE',  'Pendiente'
        ENVIADO    = 'ENVIADO',    'Enviado'
        AUTORIZADO = 'AUTORIZADO', 'Autorizado'
        RECHAZADO  = 'RECHAZADO',  'Rechazado'
        DEVUELTO   = 'DEVUELTO',   'Devuelto'

    contribuyente = models.ForeignKey(Contribuyente, on_delete=models.PROTECT, related_name='facturas')

    # Estado del ciclo de vida
    estado               = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True)
    clave_acceso         = models.CharField(max_length=49, unique=True, blank=True, db_index=True)
    numero_autorizacion  = models.CharField(max_length=49, blank=True)
    fecha_autorizacion   = models.DateTimeField(null=True, blank=True)

    # Identificación del comprobante
    establecimiento = models.CharField(max_length=3)
    punto_emision   = models.CharField(max_length=3)
    secuencial      = models.CharField(max_length=9)
    ambiente        = models.CharField(max_length=1, default='1')

    # Cliente
    cliente_identificacion      = models.CharField(max_length=20)
    cliente_tipo_identificacion = models.CharField(max_length=2, default='05')
    cliente_razon_social        = models.CharField(max_length=300)
    cliente_email               = models.EmailField(blank=True)
    cliente_direccion           = models.CharField(max_length=300, blank=True)
    cliente_telefono            = models.CharField(max_length=30, blank=True)

    # Totales
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iva      = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total    = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Payload original y archivos generados
    payload              = models.JSONField(default=dict)
    xml_path             = models.CharField(max_length=500, blank=True)
    xml_autorizado_path  = models.CharField(max_length=500, blank=True)
    pdf_path             = models.CharField(max_length=500, blank=True)

    # Trazabilidad
    mensaje_sri = models.TextField(blank=True)
    intentos    = models.PositiveSmallIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['estado', 'created_at']),
            models.Index(fields=['contribuyente', 'estado']),
        ]

    def __str__(self):
        return f'{self.numero_comprobante} · {self.estado}'

    @property
    def numero_comprobante(self):
        return f'{self.establecimiento}-{self.punto_emision}-{self.secuencial}'

    def marcar(self, estado, mensaje=''):
        self.estado = estado
        if mensaje:
            self.mensaje_sri = mensaje
        self.save(update_fields=['estado', 'mensaje_sri', 'updated_at'])
