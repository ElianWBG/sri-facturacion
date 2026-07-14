from django.contrib import admin

from .models import Contribuyente, Factura, SecuenciaFactura


@admin.register(Contribuyente)
class ContribuyenteAdmin(admin.ModelAdmin):
    list_display  = ('razon_social', 'ruc', 'ambiente', 'is_active', 'simulado', 'created_at')
    list_filter   = ('ambiente', 'is_active', 'obligado_contabilidad')
    search_fields = ('ruc', 'razon_social', 'nombre_referencia')
    readonly_fields = ('api_key', 'created_at')
    fieldsets = (
        ('Autenticación', {
            'fields': ('api_key', 'nombre_referencia', 'is_active'),
            'description': 'El API key se genera automáticamente al crear el contribuyente.',
        }),
        ('Identidad tributaria', {
            'fields': ('ruc', 'razon_social', 'nombre_comercial', 'dir_matriz',
                       'dir_establecimiento', 'codigo_establecimiento', 'punto_emision'),
        }),
        ('Configuración SRI', {
            'fields': ('ambiente', 'obligado_contabilidad', 'contribuyente_especial'),
        }),
        ('Firma electrónica', {
            'fields': ('firma_p12', 'clave_firma'),
            'description': 'Si no hay .p12 cargado, se usa firma simulada (solo válida para pruebas).',
        }),
    )

    def simulado(self, obj):
        return obj.simulado
    simulado.boolean = True
    simulado.short_description = 'Simulado'


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display  = ('numero_comprobante', 'contribuyente', 'estado', 'cliente_razon_social', 'total', 'created_at')
    list_filter   = ('estado', 'ambiente', 'contribuyente')
    search_fields = ('clave_acceso', 'cliente_identificacion', 'cliente_razon_social')
    readonly_fields = ('clave_acceso', 'numero_autorizacion', 'created_at', 'updated_at')
    raw_id_fields = ('contribuyente',)


@admin.register(SecuenciaFactura)
class SecuenciaFacturaAdmin(admin.ModelAdmin):
    list_display = ('contribuyente', 'establecimiento', 'punto_emision', 'ultimo_numero')
    readonly_fields = ('contribuyente', 'establecimiento', 'punto_emision', 'ultimo_numero')
