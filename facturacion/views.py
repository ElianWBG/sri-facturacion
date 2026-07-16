import threading
from decimal import Decimal

from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Factura
from .secuencia import siguiente_secuencial
from .serializers import FacturaEstadoSerializer, VentaEntradaSerializer
from .tasks import emitir_factura


class EmitirFacturaView(APIView):
    """
    POST /api/v1/facturas/

    Crea la factura en PENDIENTE para el contribuyente autenticado,
    responde 202 y dispara el procesamiento en segundo plano (Celery).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        contribuyente = request.user  # ApiKeyAuthentication pone el Contribuyente aquí

        serializer = VentaEntradaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subtotal = Decimal('0')
        iva      = Decimal('0')
        for it in data['items']:
            base = (it['cantidad'] * it['precio_unitario']) - it.get('descuento', 0)
            subtotal += base
            if it.get('codigo_iva', '2') == '2':
                iva += (base * Decimal('0.15')).quantize(Decimal('0.01'))

        factura = Factura.objects.create(
            contribuyente               = contribuyente,
            estado                      = Factura.Estado.PENDIENTE,
            ambiente                    = contribuyente.ambiente,
            establecimiento             = contribuyente.codigo_establecimiento,
            punto_emision               = contribuyente.punto_emision,
            secuencial                  = siguiente_secuencial(
                contribuyente,
                contribuyente.codigo_establecimiento,
                contribuyente.punto_emision,
            ),
            cliente_identificacion      = data['cliente_identificacion'],
            cliente_tipo_identificacion = data['cliente_tipo_identificacion'],
            cliente_razon_social        = data['cliente_razon_social'],
            cliente_email               = data.get('cliente_email', ''),
            cliente_direccion           = data.get('cliente_direccion', ''),
            cliente_telefono            = data.get('cliente_telefono', ''),
            subtotal                    = subtotal,
            iva                         = iva,
            total                       = subtotal + iva,
            payload                     = request.data,
        )

        threading.Thread(
            target=emitir_factura.apply,
            kwargs={'args': [factura.id]},
            daemon=True,
        ).start()

        return Response(
            FacturaEstadoSerializer(factura).data,
            status=status.HTTP_202_ACCEPTED,
        )


class FacturaEstadoView(RetrieveAPIView):
    """
    GET /api/v1/facturas/<pk>/

    Devuelve el estado actual de una factura.
    Solo puede consultar las propias del contribuyente autenticado.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FacturaEstadoSerializer

    def get_queryset(self):
        return Factura.objects.filter(contribuyente=self.request.user)
