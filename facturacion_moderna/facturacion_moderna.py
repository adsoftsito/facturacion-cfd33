# encoding: utf-8
import os
import base64
from suds import WebFault
from suds.client import Client
from lxml import etree as ET
import logging
#from suds.xsd.doctor import ImportDoctor, Import
import ssl
#import suds_requests

class Cliente:
  def __init__(self, url, opciones = {}, debug = False):
    self.debug = debug
    self.url = url
    self.opciones = {}
    if self.debug: self._activa_debug()
    print (opciones)

    for key, value in opciones.items():
      if key in ['emisorRFC', 'UserID', 'UserPass']:
        self.opciones.update({ key: value })
    print ('init client ok')
    
  def timbrar(self, src, opciones = { 'generarCBB': False, 'generarTXT': False, 'generarPDF': False}):
    try:
      # en caso de que src sea una ruta a archivo y no una cadena, abrir y cargar ruta
      print('cfdi a timbrar')
      print(src)
      src = src.encode('utf8')
      #print(src)
      #print(self)
      # print(opciones)

      logging.basicConfig(level=logging.INFO)
      if __debug__:
        #logging.getLogger('suds.client').setLevel(logging.CRITICAL)
        logging.getLogger('suds.client').setLevel(logging.DEBUG)
      else:
        logging.getLogger('suds.client').setLevel(logging.CRITICAL)

      try:
        _create_unverified_https_context = ssl._create_unverified_context
      except AttributeError:
        pass
      else:
        ssl._create_default_https_context = _create_unverified_https_context

      if os.path.isfile(src): src = open(src, 'r').read()
      #src=base64.b64decode(src).decode('utf-8')
      # b&apos;
      text2cfdi = base64.b64encode(src).decode('utf8')
      print(text2cfdi)

 
      opciones['text2CFDI'] = text2cfdi
      self.opciones.update(opciones)
      #print(opciones)      
      #print(self.url)
      #imp = Import('http://schemas.xmlsoap.org/soap/encoding/')
#      cliente = Client(self.url, doctor=ImportDoctor(imp))
      #cliente = Client(self.url, transport=suds_requests.RequestsTransport())
      cliente = Client(self.url)

      #print(cliente)
      #print(self.url)
      respuesta = cliente.service.requestTimbrarCFDI(self.opciones)

      for propiedad in ['xml', 'pdf', 'png', 'txt']:
        if propiedad in respuesta:
          self.__dict__[propiedad] = base64.b64decode(respuesta[propiedad])

      if 'xml' in respuesta:
        xml_cfdi = ET.fromstring(self.xml)
        tfd = xml_cfdi.xpath('//tfd:TimbreFiscalDigital', namespaces={"tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"})
        self.__dict__['uuid'] = tfd[0].get('UUID')

      #if self.debug:
        #self.logger.info("\nSOAP request:\n %s" % cliente.last_sent())
        #self.logger.info("\nSOAP response:\n %s" % cliente.last_received())

      return True
    except WebFault as e:
      self.__dict__['codigo_error'] = e.fault.faultcode
      self.__dict__['error'] = e.fault.faultstring
      print ("**** err *****")

      if self.debug:
        print ("**** err *****")
        self.logger.error("\nSOAP request:\n %s\nSOAP response: [%s] - %s" % (cliente.last_sent(), e.fault.faultcode, e.fault.faultstring))
        #self.logger.error("\nSOAP request:\n %s\nSOAP response: [%s] - %s" % ("--", e.fault.faultcode, e.fault.faultstring))

      return False
    except Exception as e:
      print (e)
      self.__dict__['codigo_error'] = 'Error desconocido'
      self.__dict__['error'] = e.message
      return False

  def cancelar(self, uuid):
    try:
      cliente = Client(self.url)
      opciones = {'uuid': uuid}
      opciones.update(self.opciones)
      respuesta = cliente.service.requestCancelarCFDI(opciones)
      if self.debug:
        self.logger.info("\nSOAP request:\n %s" % cliente.last_sent())
        self.logger.info("\nSOAP response:\n %s" % cliente.last_received())
      return True
    except WebFault as e:
      self.__dict__['codigo_error'] = e.fault.faultcode
      self.__dict__['error'] = e.fault.faultstring
      if self.debug:
        self.logger.error("\nSOAP request:\n %s\nSOAP response: [%s] - %s" % (cliente.last_sent(), e.fault.faultcode, e.fault.faultstring))
      return False
    except Exception as e:
      self.__dict__['codigo_error'] = 'Error desconocido'
      self.__dict__['error'] = e.message
      return False

  def activarCancelacion(self, archCer, archKey, passKey):
    try:
      # en caso de que archCer y/o archKey sean una ruta a archivo y no una cadena, abrir y cargar ruta
      if os.path.isfile(archCer): archCer = open(archCer, 'r').read()
      if os.path.isfile(archKey): archKey = open(archKey, 'r').read()
      opciones = {}
      opciones['archivoKey'] = base64.b64encode(archKey)
      opciones['archivoCer'] = base64.b64encode(archCer)
      opciones['clave'] = passKey
      self.opciones.update(opciones)
      cliente = Client(self.url)
      respuesta = cliente.service.activarCancelacion(self.opciones)
      if self.debug:
        self.logger.info("\nSOAP request:\n %s" % cliente.last_sent())
        self.logger.info("\nSOAP response:\n %s" % cliente.last_received())
      return True
    except WebFault as e:
      self.__dict__['codigo_error'] = e.fault.faultcode
      self.__dict__['error'] = e.fault.faultstring
      if self.debug:
        self.logger.error("\nSOAP request:\n %s\nSOAP response: [%s] - %s" % (cliente.last_sent(), e.fault.faultcode, e.fault.faultstring))
      return False
    except Exception as e:
      self.__dict__['codigo_error'] = 'Error desconocido'
      self.__dict__['error'] = e.message
      return False

  def _activa_debug(self):
    if not os.path.exists('log'): os.makedirs('log')
    self.logger = logging.getLogger('facturacion_moderna')
    hdlr = logging.FileHandler('log/facturacion_moderna.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    self.logger.addHandler(hdlr) 
    self.logger.setLevel(logging.INFO)
      
