"""Envío del correo al cliente con diseño HTML de la tienda."""
from decimal import Decimal
from pathlib import Path

from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags


def enviar_comprobante(*, factura, xml_path, pdf_path) -> None:
    if not factura.cliente_email:
        return

    payload = factura.payload or {}
    store_name = payload.get('store_name') or 'nuestra tienda'
    logo_url = payload.get('logo_url') or ''
    tipo_pago_label = payload.get('tipo_pago_label') or ''
    pedido_id = payload.get('pedido_id') or '-'
    factura_id_principal = payload.get('factura_id_principal')

    date_str = factura.created_at.strftime('%d/%m/%Y')
    customer_name = factura.cliente_razon_social.upper()

    rows = ''
    for item in payload.get('items', []):
        try:
            cantidad = Decimal(str(item['cantidad']))
            precio = Decimal(str(item['precio_unitario']))
            descuento = Decimal(str(item.get('descuento', 0)))
            subtotal_item = cantidad * precio - descuento
        except Exception:
            subtotal_item = Decimal('0')
        rows += (
            f'<tr style="border-bottom:1px solid #F1EEE9;">'
            f'<td style="padding:9px 12px;color:#231A10;">{item["descripcion"]}</td>'
            f'<td style="padding:9px 12px;text-align:center;color:#231A10;">{item["cantidad"]}</td>'
            f'<td style="padding:9px 12px;text-align:right;color:#231A10;">${subtotal_item:.2f}</td>'
            f'</tr>'
        )

    logo_html = ''
    if logo_url:
        logo_html = (
            f'<img src="{logo_url}" alt="{store_name}" '
            f'style="max-height:52px;max-width:200px;display:block;margin:0 auto 10px;">'
        )

    factura_num = f'#{factura_id_principal:05d}' if factura_id_principal else f'#{factura.pk}'

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:20px 0;background:#F8F4F0;font-family:Arial,Helvetica,sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#ffffff;border:1px solid #DDD5CC;border-radius:4px;overflow:hidden;">

  <!-- HEADER -->
  <div style="background:#B5441B;padding:28px 32px;text-align:center;">
    {logo_html}
    <h1 style="color:#ffffff;font-size:22px;margin:0;letter-spacing:2px;text-transform:uppercase;">{store_name}</h1>
    <p style="color:rgba(255,255,255,0.8);font-size:11px;margin:5px 0 0;letter-spacing:2px;text-transform:uppercase;">FACTURA ELECTRÓNICA</p>
  </div>

  <!-- DATE BAND -->
  <div style="background:#231A10;padding:9px 32px;text-align:center;">
    <p style="color:#F8F4F0;font-size:11px;letter-spacing:2px;margin:0;text-transform:uppercase;">PERIODO {date_str}</p>
  </div>

  <!-- CUSTOMER -->
  <div style="padding:24px 32px 20px;border-bottom:1px solid #EDE7E0;">
    <h2 style="font-size:19px;color:#231A10;margin:0 0 4px;text-transform:uppercase;letter-spacing:1px;">{customer_name}</h2>
    <p style="color:#7A6358;font-size:13px;margin:2px 0;">Cédula / RUC: {factura.cliente_identificacion}</p>
    <p style="color:#7A6358;font-size:13px;margin:2px 0;">{factura.cliente_email}</p>
  </div>

  <!-- INVOICE DETAILS BOX -->
  <div style="margin:20px 32px;border:1px solid #DDD5CC;border-radius:4px;overflow:hidden;font-size:13px;">
    <table style="width:100%;border-collapse:collapse;">
      <tr style="border-bottom:1px solid #EDE7E0;">
        <td style="padding:10px 16px;color:#7A6358;width:48%;">No. de Factura</td>
        <td style="padding:10px 16px;color:#231A10;font-weight:bold;">{factura_num}</td>
      </tr>
      <tr style="border-bottom:1px solid #EDE7E0;">
        <td style="padding:10px 16px;color:#7A6358;">Pedido</td>
        <td style="padding:10px 16px;color:#231A10;font-weight:bold;">#{pedido_id}</td>
      </tr>
      <tr style="border-bottom:1px solid #EDE7E0;">
        <td style="padding:10px 16px;color:#7A6358;">Fecha de emisión</td>
        <td style="padding:10px 16px;color:#231A10;">{date_str}</td>
      </tr>
      <tr>
        <td style="padding:10px 16px;color:#7A6358;">Forma de pago</td>
        <td style="padding:10px 16px;color:#231A10;">{tipo_pago_label}</td>
      </tr>
    </table>
  </div>

  <!-- PRODUCTS TABLE -->
  <div style="margin:0 32px 8px;">
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead>
        <tr style="background:#F1EEE9;">
          <th style="padding:9px 12px;text-align:left;color:#7A6358;font-size:10px;letter-spacing:1px;text-transform:uppercase;font-weight:700;">Producto</th>
          <th style="padding:9px 12px;text-align:center;color:#7A6358;font-size:10px;letter-spacing:1px;text-transform:uppercase;font-weight:700;">Cant.</th>
          <th style="padding:9px 12px;text-align:right;color:#7A6358;font-size:10px;letter-spacing:1px;text-transform:uppercase;font-weight:700;">Subtotal</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>

    <!-- TOTALS -->
    <table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:2px;">
      <tr>
        <td style="padding:6px 12px;text-align:right;color:#7A6358;">Subtotal sin IVA</td>
        <td style="padding:6px 12px;text-align:right;color:#231A10;width:110px;">${factura.subtotal:.2f}</td>
      </tr>
      <tr>
        <td style="padding:6px 12px;text-align:right;color:#7A6358;">IVA</td>
        <td style="padding:6px 12px;text-align:right;color:#231A10;">${factura.iva:.2f}</td>
      </tr>
      <tr style="border-top:2px solid #B5441B;">
        <td style="padding:12px 12px;text-align:right;font-weight:bold;font-size:17px;color:#B5441B;">TOTAL</td>
        <td style="padding:12px 12px;text-align:right;font-weight:bold;font-size:17px;color:#B5441B;">${factura.total:.2f}</td>
      </tr>
    </table>
  </div>

  <!-- FOOTER -->
  <div style="background:#231A10;padding:20px 32px;text-align:center;margin-top:12px;">
    <p style="color:#F8F4F0;font-size:12px;margin:0 0 4px;">Gracias por confiar en <strong>{store_name}</strong>.</p>
    <p style="color:rgba(255,255,255,0.5);font-size:11px;margin:0;">Los archivos adjuntos incluyen tu factura en PDF y XML.</p>
  </div>

</div>
</body>
</html>"""

    message = EmailMultiAlternatives(
        subject=f'Pedido #{pedido_id} confirmado',
        body=strip_tags(html_content),
        to=[factura.cliente_email],
    )
    message.attach_alternative(html_content, 'text/html')

    if xml_path and Path(xml_path).exists():
        message.attach_file(str(xml_path))
    if pdf_path and Path(pdf_path).exists():
        message.attach_file(str(pdf_path))

    message.send(fail_silently=False)
