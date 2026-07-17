import base64
import os

from rest_framework import serializers

from .models import Factura


class ItemVentaSerializer(serializers.Serializer):
    codigo          = serializers.CharField(max_length=25)
    descripcion     = serializers.CharField(max_length=300)
    cantidad        = serializers.DecimalField(max_digits=14, decimal_places=6)
    precio_unitario = serializers.DecimalField(max_digits=14, decimal_places=6)
    descuento       = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)
    # Código de porcentaje de IVA del SRI: 0=0%, 2=12/15%, 6=No objeto, 7=Exento
    codigo_iva      = serializers.CharField(max_length=2, required=False, default='2')


class VentaEntradaSerializer(serializers.Serializer):
    """Payload que envía el sistema principal al emitir una factura."""

    cliente_identificacion      = serializers.CharField(max_length=20)
    cliente_tipo_identificacion = serializers.CharField(max_length=2, default='05')
    cliente_razon_social        = serializers.CharField(max_length=300)
    cliente_email               = serializers.EmailField(required=False, allow_blank=True)
    cliente_direccion           = serializers.CharField(max_length=300, required=False, allow_blank=True)
    cliente_telefono            = serializers.CharField(max_length=30, required=False, allow_blank=True)
    items                       = ItemVentaSerializer(many=True)
    enviar_email                = serializers.BooleanField(required=False, default=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('La venta debe tener al menos un ítem.')
        return value


class FacturaEstadoSerializer(serializers.ModelSerializer):
    numero_comprobante = serializers.CharField(read_only=True)
    contribuyente_ruc  = serializers.CharField(source='contribuyente.ruc', read_only=True)
    xml                = serializers.SerializerMethodField()

    class Meta:
        model = Factura
        fields = [
            'id', 'contribuyente_ruc', 'estado', 'clave_acceso',
            'numero_comprobante', 'numero_autorizacion', 'mensaje_sri', 'created_at',
            'xml',
        ]

    def get_xml(self, obj):
        path = obj.xml_autorizado_path or obj.xml_path
        if not path or not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
