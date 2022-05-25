#
# -*- coding: utf-8 -*-

import logging
import sys
import unittest
from six import StringIO
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

from xmllayout import XMLLayout, DEFAULT_MDC_RE

PY3 = sys.version_info >= (3,)

LOG4J_NS = 'http://jakarta.apache.org/log4j/'

log = logging.getLogger(__name__)
stream = StringIO()
handler = logging.StreamHandler(stream)
xmllayout = XMLLayout(mdcre=DEFAULT_MDC_RE)
handler.setFormatter(xmllayout)
log.addHandler(handler)
log.setLevel(logging.DEBUG)


class ElvisException(Exception):
    def __init__(self, info):
        self.info = info

    def __str__(self):
        return "<ElvisException: %s (TCB because he's the king baby)>" % \
            self.info


def test_xmllayout():
    _test_output('')
    _test_output('hello')
    _test_output('hello world', level=logging.DEBUG)
    _test_output('hello world!', level=logging.WARN, log4jlevel='WARN')
    _test_output('hello, world!', level=logging.WARNING, log4jlevel='WARN')
    _test_output('hello, world!!', level=logging.CRITICAL, log4jlevel='FATAL')
    _test_output('<xml><something>&nbsp;Hi</something></xml>')
    _test_output("""\
{'CONTENT_LENGTH': '0',
 'CONTENT_TYPE': '',
 'HTTP_ACCEPT': '*/*',
 'HTTP_ACCEPT_ENCODING': 'gzip, deflate',
 'HTTP_ACCEPT_LANGUAGE': 'en',
 'HTTP_CONNECTION': 'keep-alive',
 'HTTP_COOKIE': ''
 'HTTP_HOST': 'bob.local:5000',
 'HTTP_USER_AGENT': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en) AppleWebKit/419.2.1 (KHTML, like Gecko) Safari/419.3',
 'PATH_INFO': '/hello',
 'QUERY_STRING': '',
 'REMOTE_ADDR': '192.168.1.111',
 'REQUEST_METHOD': 'GET',
 'SCRIPT_NAME': '',
 'SERVER_NAME': '0.0.0.0',
 'SERVER_PORT': '5000',
 'SERVER_PROTOCOL': 'HTTP/1.1',
 'paste.evalexception': <pylons.error.PylonsEvalException object at 0x8c75ccc>,
 'wsgi.errors': <open file '<stderr>', mode 'w' at 0x81280b0>,
 'wsgi.input': <socket._fileobject object at 0x8c7a48c length=0>,
 'wsgi.multiprocess': False,
 'wsgi.multithread': True,
 'wsgi.run_once': False,
 'wsgi.url_scheme': 'http',
 'wsgi.version': (1, 0),}
""")


def test_exceptions():
    try:
        raise ElvisException('dog')
    except ElvisException:
        exc_module = ''
        if PY3:
            exc_module = ElvisException.__module__ + '.'
        exc_msg = ("raise ElvisException('dog')\n%sElvisException: "
                   "<ElvisException: dog (TCB because he's the king baby)>" %
                   exc_module)
        _test_output('Elvis has left the building', exc_info=True,
                     exc_msg=exc_msg)


def test_exceptions_cdata():
    exc_msg = 'Hello ]]> World!'
    try:
        raise ElvisException(exc_msg)
    except ElvisException:
        _test_output('Elvis has left the building', exc_info=True,
                     exc_msg=exc_msg)


def test_mdc():
    mdc = {"mdc:a_mdc_key": r"""A Value with "' and german umlaut ÄÖÜäöüß§ &"""}
    _test_output("message", extra=mdc)


def get_output():
    output = stream.getvalue().rstrip()
    stream.seek(0)
    stream.truncate(0)
    return '<test xmlns:log4j="%s">%s</test>' % (LOG4J_NS, output)


def _test_output(message, level=logging.INFO, log4jlevel=None, exc_info=None,
                 exc_msg=None, extra={}):
    if log4jlevel is None:
        log4jlevel = logging.getLevelName(level)
    log.log(level, message, **dict(exc_info=exc_info, extra=extra))
    output = get_output()
    tree = ET.XML(output)

    event = tree.find("{%s}event" % LOG4J_NS)
    xml_level = event.get('level')
    assert xml_level == log4jlevel, message
    xml_message = tree.findtext("{%s}event/{%s}message" % (LOG4J_NS, LOG4J_NS))
    assert message == xml_message, message

    if exc_info:
        xml_exc = tree.findtext("{%s}event/{%s}throwable" % (LOG4J_NS,
                                                             LOG4J_NS))
        assert exc_msg in xml_exc, message
    if extra:
        xml_data = tree.find("{%s}event/{%s}properties/{%s}data" % (LOG4J_NS,
                                                                    LOG4J_NS,
                                                                    LOG4J_NS))
        assert 'mdc:' + xml_data.get('name') == list(extra.keys())[0]
        assert xml_data.get('value') == list(extra.values())[0]


class Test(unittest.TestCase):
    def test_xmllayout(self):
        test_xmllayout()

    def test_exceptions(self):
        test_exceptions()

    def test_exceptions_cdata(self):
        test_exceptions_cdata()

    def test_mdc(self):
        test_mdc()
