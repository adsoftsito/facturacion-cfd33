# encoding: utf-8
from flask import Flask, request, make_response
from flask_cors import CORS, cross_origin

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
import requests

sys.setdefaultencoding('utf8')

app = Flask(__name__,
           static_url_path='',
           static_folder='comprobantes')

#CORS(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
#cors = CORS(app)
#app.config['CORS_HEADERS'] = 'Content-Type'
#app.config['CORS_HEADERS'] = 'Access-Control-Allow-Headers'

mycomprobante="";
content="";

def prueba_timbrado(debug = False):
  
  # RFC utilizado para el ambiente de pruebas
  rfc_emisor = "ESI920427886"

  url = 'http://18.116.12.129:8082/graphql/'
  json= {'query' : '{ emisorcer(rfc:"CETA761021") { certificado filekey }}' }
  r = requests.post(url=url, json=json)
  print(r.json()) 

  
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
    return 'ok'
  else:
    print ("error timbrar ")
    print("[%s] - %s" % (cliente.codigo_error, cliente.error))
    return cliente.error

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
  totaldescuento=content["descuento"] 
  moneda=content["moneda"] 
  total=content["total"] 
  tipodecomprobante=content["tipodecomprobante"] 
  metodopago=content["metodopago"] 
  lugarexpedicion=content["lugarexpedicion"] 
  emisor = content["emisor"]
  receptor = content["receptor"]
  conceptos = content["conceptos"]
  total_impuestos = content["impuestos"]
  total_impuestos_trasladados = total_impuestos["totalimpuestostrasladados"]
  total_traslados = total_impuestos["traslados"]

  #print("== total impuestos trasladados ==")
  #print(total_impuestos_trasladados)

  # print (total_traslados)
  mytotal_traslados = ""

  for totaltraslado in total_traslados:
    # base = traslado["base"]
    totaltraslado_impuesto = totaltraslado["impuesto"]
    totaltraslado_tipofactor = totaltraslado["tipofactor"]
    totaltraslado_tasaocuota = totaltraslado["tasaocuota"]
    totaltraslado_importe = totaltraslado["importe"]

    mytotal_traslados= mytotal_traslados + """<cfdi:Traslado Impuesto="{totaltraslado_impuesto}" TipoFactor="{totaltraslado_tipofactor}" TasaOCuota="{totaltraslado_tasaocuota}" Importe="{totaltraslado_importe}"/>""".format(**locals())

  if mytotal_traslados != "":
      mytotal_traslados = "<cfdi:Traslados>" + mytotal_traslados + "</cfdi:Traslados>"
  #print("total traslados ...")
  print(mytotal_traslados)



  myconceptos=""
  for concepto in conceptos:
    claveprodserv = concepto["claveprodserv"]
    noidentificacion = concepto["noidentificacion"]
    cantidad = concepto["cantidad"]
    claveunidad = concepto["claveunidad"]
    unidad = concepto["unidad"]
    descripcion = concepto["descripcion"]
    valorunitario = concepto["valorunitario"]
    concepto_importe = concepto["importe"]
    descuento = concepto["descuento"]
    impuestos = concepto["impuestos"]
    print('impuestos ---')
    traslados = impuestos["traslados"]
    retenciones = impuestos["retenciones"]

    # print(traslados)
    mytraslados=""

    for traslado in traslados:
      base = traslado["base"]
      impuesto = traslado["impuesto"]
      tipofactor = traslado["tipofactor"]
      tasaocuota = traslado["tasaocuota"]
      traslado_importe = traslado["importe"]

      mytraslados= mytraslados + """<cfdi:Traslado Base="{base}" Impuesto="{impuesto}" TipoFactor="{tipofactor}" TasaOCuota="{tasaocuota}" Importe="{traslado_importe}"/>""".format(**locals())
    if mytraslados != "":
      mytraslados = "<cfdi:Traslados>" + mytraslados + "</cfdi:Traslados>"
    #print(" traslados ...")
    #print(mytraslados)
  
    myconceptos=myconceptos+"""<cfdi:Concepto ClaveProdServ="{claveprodserv}" NoIdentificacion="{noidentificacion}" Cantidad="{cantidad}" ClaveUnidad="{claveunidad}" Unidad="{unidad}" Descripcion="{descripcion}" ValorUnitario="{valorunitario}" Importe="{concepto_importe}" Descuento="{descuento}">
      <cfdi:Impuestos>
       {mytraslados}  
</cfdi:Impuestos>
</cfdi:Concepto>
""".format(**locals())
  #print("conceptos - traslados")
  #print(myconceptos)

  emisor_rfc = rfc_emisor #emisor["rfc"] 
  emisor_nombre = emisor["nombre"]
  emisor_regimenfiscal = emisor["regimenfiscal"]

  receptor_rfc = receptor["rfc"] 
  receptor_nombre = receptor["nombre"]
  receptor_usocfdi = receptor["usocfdi"]


  #print('conceptos')
  #print(conceptos)
  #print('----------')
  cfdi = """<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/3" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv33.xsd" Version="3.3" Serie="{serie}" Folio="{folio}" Fecha="{fecha_actual}" Sello="" FormaPago="{formapago}" NoCertificado="" Certificado="" CondicionesDePago="{condicionesdepago}" SubTotal="{subtotal}" Descuento="{totaldescuento}" Moneda="{moneda}" Total="{total}" TipoDeComprobante="{tipodecomprobante}" MetodoPago="{metodopago}" LugarExpedicion="{lugarexpedicion}">
  <cfdi:Emisor Rfc="{emisor_rfc}" Nombre="{emisor_nombre}" RegimenFiscal="{emisor_regimenfiscal}"/>
  <cfdi:Receptor Rfc="{receptor_rfc}" Nombre="{receptor_nombre}" UsoCFDI="{receptor_usocfdi}"/>
  <cfdi:Conceptos>{myconceptos}</cfdi:Conceptos>
<cfdi:Impuestos TotalImpuestosTrasladados="{total_impuestos_trasladados}">
{mytotal_traslados}
</cfdi:Impuestos>
</cfdi:Comprobante>
""".format(**locals())
  print ("cfdi ok")

  #xdoc = ET.fromstring(cfdi)
  #conceptos = xdoc.xpath('//cfdi:Comprobante/cfdi:Conceptos')
  #print(conceptos)
 # conceptos = ET.SubElement(xdoc, 'Conceptos')
  #print(ET.tostring(conceptos, pretty_print=True))
  #cfdi = ET.tostring(xdoc)
  # print(ET.tostring(xdoc, pretty_print=True))
  print(cfdi)
  print("=========")

  return cfdi



@app.route('/', methods=['POST','OPTIONS'])
def hello_world():
  print (request.method)
  if request.method == "OPTIONS": # CORS preflight
    return _build_cors_prelight_response()

  global serie, folio, content
  print (request)
  content = request.json
  print (content)
  #content = json.dumps(content)
#  serie = content["serie"]
#  folio = content["folio"]
#  print (serie)
#  print (folio)


  try:
    myres = prueba_timbrado()
    result = (request.host_url) + mycomprobante
    print (' resultado : ', myres)
    if (myres=='ok'):
      data_set = {"xml": result + '.xml', "pdf": result + '.pdf'}
    else:
      data_set = {"error":  myres}
      
  except WebFault, e:
    print ("error web ", e);

  except Exception, e:
    print ("error exception ", e)

  return json.dumps(data_set)

def _build_cors_prelight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response


if __name__ == "__main__":
  app.run(host='0.0.0.0')
