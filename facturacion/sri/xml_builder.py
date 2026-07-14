"""Construcción del XML de la factura versión 1.1.0 según esquema del SRI."""
from decimal import Decimal
from xml.etree import ElementTree as ET


def _t(parent, tag, text):
    el = ET.SubElement(parent, tag)
    el.text = '' if text is None else str(text)
    return el


def _money(value) -> str:
    return f'{Decimal(value).quantize(Decimal("0.01"))}'


def construir_xml_factura(*, emisor: dict, factura, items: list[dict], clave_acceso: str) -> bytes:
    root = ET.Element('factura', {'id': 'comprobante', 'version': '1.1.0'})

    info_trib = ET.SubElement(root, 'infoTributaria')
    _t(info_trib, 'ambiente',        factura.ambiente)
    _t(info_trib, 'tipoEmision',     '1')
    _t(info_trib, 'razonSocial',     emisor['RAZON_SOCIAL'])
    _t(info_trib, 'nombreComercial', emisor['NOMBRE_COMERCIAL'])
    _t(info_trib, 'ruc',             emisor['RUC'])
    _t(info_trib, 'claveAcceso',     clave_acceso)
    _t(info_trib, 'codDoc',          '01')
    _t(info_trib, 'estab',           factura.establecimiento)
    _t(info_trib, 'ptoEmi',          factura.punto_emision)
    _t(info_trib, 'secuencial',      factura.secuencial)
    _t(info_trib, 'dirMatriz',       emisor['DIR_MATRIZ'])

    info_fac = ET.SubElement(root, 'infoFactura')
    _t(info_fac, 'fechaEmision',               factura.created_at.strftime('%d/%m/%Y'))
    _t(info_fac, 'dirEstablecimiento',          emisor['DIR_ESTABLECIMIENTO'])
    if emisor.get('CONTRIBUYENTE_ESPECIAL'):
        _t(info_fac, 'contribuyenteEspecial',  emisor['CONTRIBUYENTE_ESPECIAL'])
    _t(info_fac, 'obligadoContabilidad',        emisor.get('OBLIGADO_CONTABILIDAD', 'NO'))
    _t(info_fac, 'tipoIdentificacionComprador', factura.cliente_tipo_identificacion)
    _t(info_fac, 'razonSocialComprador',        factura.cliente_razon_social)
    _t(info_fac, 'identificacionComprador',     factura.cliente_identificacion)
    _t(info_fac, 'totalSinImpuestos',           _money(factura.subtotal))
    _t(info_fac, 'totalDescuento',              '0.00')

    total_imp = ET.SubElement(info_fac, 'totalConImpuestos')
    ti = ET.SubElement(total_imp, 'totalImpuesto')
    _t(ti, 'codigo',           '2')
    _t(ti, 'codigoPorcentaje', '4')
    _t(ti, 'baseImponible',    _money(factura.subtotal))
    _t(ti, 'valor',            _money(factura.iva))

    _t(info_fac, 'propina',       '0.00')
    _t(info_fac, 'importeTotal',  _money(factura.total))
    _t(info_fac, 'moneda',        'DOLAR')

    pagos = ET.SubElement(info_fac, 'pagos')
    pago = ET.SubElement(pagos, 'pago')
    _t(pago, 'formaPago', '01')
    _t(pago, 'total',     _money(factura.total))

    detalles = ET.SubElement(root, 'detalles')
    for it in items:
        base = (Decimal(str(it['cantidad'])) * Decimal(str(it['precio_unitario']))) - Decimal(str(it.get('descuento', 0)))
        det = ET.SubElement(detalles, 'detalle')
        _t(det, 'codigoPrincipal',          it['codigo'])
        _t(det, 'descripcion',              it['descripcion'])
        _t(det, 'cantidad',                 f'{Decimal(str(it["cantidad"])):.6f}')
        _t(det, 'precioUnitario',           f'{Decimal(str(it["precio_unitario"])):.6f}')
        _t(det, 'descuento',                _money(it.get('descuento', 0)))
        _t(det, 'precioTotalSinImpuesto',   _money(base))
        impuestos = ET.SubElement(det, 'impuestos')
        imp = ET.SubElement(impuestos, 'impuesto')
        _t(imp, 'codigo',           '2')
        _t(imp, 'codigoPorcentaje', '4')
        _t(imp, 'tarifa',           '15.00')
        _t(imp, 'baseImponible',    _money(base))
        _t(imp, 'valor',            _money((base * Decimal('0.15')).quantize(Decimal('0.01'))))

    if factura.cliente_email:
        adic = ET.SubElement(root, 'infoAdicional')
        campo = ET.SubElement(adic, 'campoAdicional', {'nombre': 'email'})
        campo.text = factura.cliente_email

    return ET.tostring(root, encoding='UTF-8', xml_declaration=True)
