# encoding: utf-8
from flask import Flask, request

from facturacion_moderna import facturacion_moderna
from datetime import datetime, timedelta
import base64
from M2Crypto import RSA
from lxml import etree as ET
import hashlib
import os
import json
import sys
reload(sys)
sys.setdefaultencoding('utf8')

app = Flask(__name__,
           static_url_path='',
           static_folder='comprobantes')

mycomprobante="";
content="";

def prueba_timbrado(debug = False):
  
  # RFC utilizado para el ambiente de pruebas
  rfc_emisor = "ESI920427886"
  
  # Archivos del CSD de prueba proporcionados por el SAT.
  # ver http://developers.facturacionmoderna.com/webroot/CertificadosDemo-FacturacionModerna.zip
  numero_certificado = "20001000000200000192"
  archivo_cer = "utilerias/certificados/20001000000200000192.cer"
  archivo_pem = "utilerias/certificados/20001000000200000192.key.pem"
  
  # Datos de acceso al ambiente de pruebas
  url_timbrado = "https://t1demo.facturacionmoderna.com/timbrado/wsdl"
  user_id = "UsuarioPruebasWS"
  user_password = "b9ec2afa3361a59af4b4d102d3f704eabdf097d4"

  cfdi = genera_xml(rfc_emisor)
  cfdi = sella_xml(cfdi, numero_certificado, archivo_cer, archivo_pem)

  params = {'emisorRFC': rfc_emisor, 'UserID': user_id, 'UserPass': user_password}
  options = {'generarCBB': False, 'generarPDF': True, 'generarTXT': False}
  cliente = facturacion_moderna.Cliente(url_timbrado, params, debug)

  if cliente.timbrar(cfdi, options):
    print ('timbre ok')
    folder = 'comprobantes'
    if not os.path.exists(folder): os.makedirs(folder)
    comprobante = os.path.join(folder, cliente.uuid)
    #print (comprobante)

    global mycomprobante
    mycomprobante = cliente.uuid

    #print(mycomprobante)

    for extension in ['xml', 'pdf', 'png', 'txt']:
      if hasattr(cliente, extension):
        with open(("%s.%s" % (comprobante, extension)), 'wb' if extension in ['pdf','png'] else 'w') as f: f.write(getattr(cliente, extension))
        print("%s almacenado correctamente en %s.%s" % (extension.upper(), comprobante, extension))
    print 'Timbrado exitoso'
  else:
    print("[%s] - %s" % (cliente.codigo_error, cliente.error))


def sella_xml(cfdi, numero_certificado, archivo_cer, archivo_pem):
  keys = RSA.load_key(archivo_pem)
  cert_file = open(archivo_cer, 'r')
  cert = base64.b64encode(cert_file.read())
  xdoc = ET.fromstring(cfdi)

  comp = xdoc.get('Comprobante')
  xdoc.attrib['Certificado'] = cert
  xdoc.attrib['NoCertificado'] = numero_certificado

  xsl_root = ET.parse('utilerias/xslt33/cadenaoriginal_3_3.xslt')
  xsl = ET.XSLT(xsl_root)
  cadena_original = xsl(xdoc)
  digest = hashlib.new('sha256', str(cadena_original)).digest()
  sello = base64.b64encode(keys.sign(digest, "sha256"))

  comp = xdoc.get('Comprobante')
  xdoc.attrib['Sello'] = sello
  
  #print (ET.tostring(xdoc))
  #print ('sello ok')
  return ET.tostring(xdoc)

def genera_xml(rfc_emisor):
  # se calcula la fecha de emisión en formato ISO 8601
  fecha_actual = str(  (datetime.now() - timedelta(hours=6, minutes=0)).isoformat())[:19]
  # fecha_actual = str(datetime.now(pytz.timezone('US/Pacific')))

  serie = content["serie"]
  folio = content["folio"]
  #print (serie)
  #print (folio)
  formapago=content["formapago"]
  condicionesdepago=content["condicionesdepago"]
  subtotal=content["subtotal"] 
  descuento=content["descuento"] 
  moneda=content["moneda"] 
  total=content["total"] 
  tipodecomprobante=content["tipodecomprobante"] 
  metodopago=content["metodopago"] 
  lugarexpedicion=content["lugarexpedicion"] 
  emisor = content["emisor"]
  receptor = content["receptor"]

  #print (emisor)

  emisor_rfc = rfc_emisor #emisor["rfc"] 
  emisor_nombre = emisor["nombre"]
  emisor_regimenfiscal = emisor["regimenfiscal"]

  receptor_rfc = receptor["rfc"] 
  receptor_nombre = receptor["nombre"]
  receptor_usocfdi = receptor["usocfdi"]

  cfdi = """<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/3" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv33.xsd" Version="3.3" Serie="{serie}" Folio="{folio}" Fecha="{fecha_actual}" Sello="" FormaPago="{formapago}" NoCertificado="" Certificado="" CondicionesDePago="{condicionesdepago}" SubTotal="{subtotal}" Descuento="{descuento}" Moneda="{moneda}" Total="{total}" TipoDeComprobante="{tipodecomprobante}" MetodoPago="{metodopago}" LugarExpedicion="{lugarexpedicion}">
  <cfdi:Emisor Rfc="{emisor_rfc}" Nombre="{emisor_nombre}" RegimenFiscal="{emisor_regimenfiscal}"/>
  <cfdi:Receptor Rfc="{receptor_rfc}" Nombre="{receptor_nombre}" UsoCFDI="{receptor_usocfdi}"/>
  <cfdi:Conceptos>
    <cfdi:Concepto ClaveProdServ="01010101" NoIdentificacion="AULOG001" Cantidad="5" ClaveUnidad="H87" Unidad="Pieza" Descripcion="Aurriculares USB Logitech" ValorUnitario="350.00" Importe="1750.00" Descuento="175.00">
      <cfdi:Impuestos>
        <cfdi:Traslados>
          <cfdi:Traslado Base="1575.00" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="252.00"/>
      </cfdi:Traslados>
  </cfdi:Impuestos>
</cfdi:Concepto>
<cfdi:Concepto ClaveProdServ="43201800" NoIdentificacion="USB" Cantidad="1" ClaveUnidad="H87" Unidad="Pieza" Descripcion="Memoria USB 32gb marca Kingston" ValorUnitario="100.00" Importe="100.00">
  <cfdi:Impuestos>
    <cfdi:Traslados>
      <cfdi:Traslado Base="100.00" Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="16.00"/>
  </cfdi:Traslados>
</cfdi:Impuestos>
</cfdi:Concepto>
</cfdi:Conceptos>
<cfdi:Impuestos TotalImpuestosTrasladados="268.00">
    <cfdi:Traslados>
      <cfdi:Traslado Impuesto="002" TipoFactor="Tasa" TasaOCuota="0.160000" Importe="268.00"/>
  </cfdi:Traslados>
</cfdi:Impuestos>
</cfdi:Comprobante>
""".format(**locals())
  #print ("cfdi ok")

  xdoc = ET.fromstring(cfdi)
  #conceptos = xdoc.xpath('//cfdi:Comprobante/cfdi:Conceptos')
  print(conceptos)
 # conceptos = ET.SubElement(xdoc, 'Conceptos')
  #print(ET.tostring(conceptos, pretty_print=True))
  cfdi = ET.tostring(xdoc)
  # print(ET.tostring(xdoc, pretty_print=True))
  print(cfdi)

  return cfdi


@app.route('/', methods=['GET','POST'])
def hello_world():
  global serie, folio, content
  content = request.json
  #print (content)
  #content = json.dumps(content)
#  serie = content["serie"]
#  folio = content["folio"]
#  print (serie)
#  print (folio)

  prueba_timbrado()
  result = (request.host_url) + mycomprobante

  data_set = {"xml": result + '.xml', "pdf": result + '.pdf'}

  return json.dumps(data_set)

if __name__ == "__main__":
  app.run(host='0.0.0.0')
