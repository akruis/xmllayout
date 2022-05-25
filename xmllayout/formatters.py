"""logging Formatters"""
import logging
import re
import codecs

__all__ = ['XMLLayout', 'REPLACEMENT_CHAR', 'DEFAULT_MDC_RE']

REPLACEMENT_CHAR = u'\ufffd'
DEFAULT_MDC_RE = re.compile(u'mdc:(?P<name>.*)')

# Level names differ slightly in log4j, see
# http://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/Level.html
LOG4J_LEVELS = dict(WARNING='WARN', CRITICAL='FATAL')


class XMLLayout(logging.Formatter):

    """Formats log Records as XML according to the `log4j XMLLayout
    <http://logging.apache.org/log4j/docs/api/org/apache/log4j/xml/
    XMLLayout.html>_`
    """
    def __init__(self, fmt=None, datefmt=None, mdcre=None, ndc=None, xmlencoding=None, non_xml_char_repl=None, withoutLocationInfo=None, layout=None):
        """Arguments: `fmt` and `datefmt` are passed to the `__init__` method of the base
        class. The argument `mdcre` is used to compute the
        log4j Mapped Diagnostic Context (MDC). `mdcre` must be a regular expression string
        or a compiled regular expression object. It must contain a named match group with name
        `name`. If the regular expression matches the name of an attribute of the log record, the
        attribute value is added to the MDC using the name given by the named match group.
        The argument 'ndc' gives the name of an attribute of the log record, that is used as
        log4j 'Nested Diagnostic Context'. The `xmlencoding` argument names an encoding
        for the XML message. The `non_xml_char_repl` argument determines how to handle
        characters, that are illegal in XML. If `non_xml_char_repl` is a string, its value
        is substituted for each illegal character. Otherwise it must be a callable object,
        that takes a regular expression match object as its sole argument and returns the
        replacement for the matched regular expression.
        If the argument 'withoutLocationInfo' is true, omit the location info.
        The layout argument must be a dictionary with format strings. The keys are 'EVENT',
        'MESSAGE', 'NDC', 'PROPERTIES', 'DATA', 'THROWABLE' and 'LOCATIONINFO'. Additionally
        the value of layout can be the name of a predefined layout either 'LAYOUT_FULL',
        'LAYOUT_COMPACT' or 'LAYOUT_DEFAULT'.
        """
        super(XMLLayout, self).__init__(fmt, datefmt)

        if not isinstance(mdcre, re.Pattern):
            mdcre = re.compile(mdcre)
        self.mdcre = mdcre

        self.ndc = ndc

        if xmlencoding is not None:
            factory = codecs.getincrementalencoder(xmlencoding)
            self.encoder = factory('xmlcharrefreplace')
        else:
            self.encoder = None

        options = {'REPLACEMENT_CHAR': REPLACEMENT_CHAR, 'STRIP': ''}
        non_xml_char_repl = options.get(non_xml_char_repl, non_xml_char_repl)
        self.non_xml_char_repl = non_xml_char_repl

        self.withLocationInfo = not bool(withoutLocationInfo)

        if layout is None:
            layout = LAYOUT_DEFAULT
        if isinstance(layout, str):
            layout = globals()[layout]
        self.layout = layout

    def format(self, record):
        """Format the log record as XMLLayout XML"""
        levelname = LOG4J_LEVELS.get(record.levelname, record.levelname)
        event = dict(name=self.escape_AttValue(record.name),
                     threadName=self.escape_AttValue(record.threadName),
                     levelname=self.escape_AttValue(levelname),
                     created=int(record.created * 1000))

        event['message'] = self.layout['MESSAGE'] % self.escape_CharData(record.getMessage())

        event['ndc'] = ''
        ndc = self.get_ndc(record)
        if ndc:
            event['ndc'] = self.layout['NDC'] % self.escape_CharData(ndc)

        # MDC data is stored within a <log4j:properties> element
        event['properties'] = ''
        mdc = self.get_mdc(record)
        if mdc:
            keys = list(mdc.keys())
            keys.sort()
            data = "".join(self.layout['DATA'] % (self.escape_AttValue(k), self.escape_AttValue(mdc[k])) for k in keys)
            event['properties'] = self.layout['PROPERTIES'] % data

        event['throwable'] = ''
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            event['throwable'] = (self.layout['THROWABLE'] %
                                  self.escape_CharData(record.exc_text))

        if self.withLocationInfo:
            location_info = dict(pathname=self.escape_AttValue(record.pathname),
                                 lineno=record.lineno,
                                 module=self.escape_AttValue(record.module), funcName='')
            if hasattr(record, 'funcName'):
                # >= Python 2.5
                location_info['funcName'] = self.escape_AttValue(record.funcName)
            event['locationInfo'] = self.layout['LOCATIONINFO'] % location_info
        else:
            event['locationInfo'] = ''

        unicode_msg = self.layout['EVENT'] % event

        if self.encoder is None:
            return unicode_msg

        return self.encoder.encode(unicode_msg, True)

    def get_ndc(self, record):
        try:
            if self.ndc:
                return getattr(record, self.ndc)
        except Exception:
            pass
        return ''

    def get_mdc(self, record):
        mdc = {}
        if self.mdcre is not None:
            for k in dir(record):
                match = self.mdcre.match(k)
                if match is not None:
                    try:
                        mdc[match.group('name')] = getattr(record, k)
                    except Exception:
                        pass
        return mdc

    # RE from http://lsimons.wordpress.com/2011/03/17/stripping-illegal-characters-out-of-xml-in-python/
    # Jython fails to parse u'\ud800' and u'\udfff'
    _illegal_xml_char_RE = u'[\x00-\x08\x0b\x0c\x0e-\x1f' + chr(0xd800) + u'-' + chr(0xdfff) + u'\ufffe\uffff]'
    _illegal_xml_char_RE = re.compile(_illegal_xml_char_RE)

    def handle_non_characters(self, string):
        """convert 'string' to a unicode string containing
        only valid xml characters.
        """
        if not isinstance(string, str):
            try:
                string = str(string)
            except UnicodeDecodeError:
                # the default encoding can't handle this string
                # We must use a different one.
                # Most probably the string is either encoded in UTF-8 or in an
                # single-byte-encoding like ISO-8859-x or CP1252 or the string
                # does not contain text, but data octets.
                # We can try UTF-8 and if that fails, we know that the string is
                # not using UTF-8. But there is no easy way to detect the right encoding.
                # If we assume, that string does not contain text but binary data,
                # the iso-8859-1 encoding is correct, because this encoding maps
                # the data-bytes the unicode codepoints with the same numerical
                # value and can decode every octet sequence.
                # If the string is long enough, we could use the chardet module,
                # but most times the string will be short.
                try:
                    string = str(string, "UTF-8")
                except UnicodeDecodeError:
                    string = str(string, "ISO-8859-1")
        if self.non_xml_char_repl is None:
            return string
        return self._illegal_xml_char_RE.sub(self.non_xml_char_repl, string)

    _whitespace_RE = re.compile(u'[\x00-\x1f]')

    @staticmethod
    def _chartoentity(matchexpr):
        return u"&#%d;" % ord(matchexpr.group())

    def handle_whitespace(self, xml_string):
        """convert whitespace to character entities if required"""
        return self._whitespace_RE.sub(self._chartoentity, xml_string)

    def escape_CharData(self, chardata):
        """escape char data

        Production 14 of W3C TR http://www.w3.org/TR/xml/
        """
        # fix illegal characters.
        chardata = self.handle_non_characters(chardata)
        chardata = chardata.replace('&', '&amp;').replace('<', '&lt;').replace(']]>', ']]&gt;')
        return self.handle_whitespace(chardata)

    def escape_AttValue(self, attvalue):
        """escape an attribute value

        Production 10 of W3C TR http://www.w3.org/TR/xml/
        """
        attvalue = self.handle_non_characters(attvalue)
        attvalue = attvalue.replace('&', '&amp;').replace('<', '&lt;').replace('"', '&quot;')
        return self.handle_whitespace(attvalue)


LAYOUT_FULL = dict(

    # General logging information
    EVENT="""\
    <log4j:event logger="%(name)s"
        timestamp="%(created)i"
        level="%(levelname)s"
        thread="%(threadName)s">
    %(message)s%(ndc)s%(throwable)s%(locationInfo)s%(properties)s</log4j:event>
    """,

    # The actual log message
    MESSAGE="""\
        <log4j:message>%s</log4j:message>
    """,

    # log4j's 'Nested Diagnostic Context': additional, customisable information
    # included with the log record
    NDC="""\
        <log4j:ndc>%s</log4j:ndc>
    """,

    # log4j's 'Mapped Diagnostic Context': additional, customisable information
    # included with the log record
    PROPERTIES="""\
        <log4j:properties>
    %s    </log4j:properties>
    """,

    DATA="""\
          <log4j:data name="%s" value="%s"/>
    """,

    # Exception information, if exc_info was included with the record
    THROWABLE="""\
        <log4j:throwable>%s</log4j:throwable>
    """,

    # Traceback information
    LOCATIONINFO="""\
        <log4j:locationInfo class="%(module)s"
            method="%(funcName)s"
            file="%(pathname)s"
            line="%(lineno)d"/>
    """
)

LAYOUT_COMPACT = dict(

    # General logging information
    EVENT="""<event logger="%(name)s" timestamp="%(created)i" level="%(levelname)s" thread="%(threadName)s">%(message)s%(ndc)s%(throwable)s%(locationInfo)s%(properties)s</event>
""",

    # The actual log message
    MESSAGE="""
<message>%s</message>""",

    # log4j's 'Nested Diagnostic Context': additional, customisable information
    # included with the log record
    NDC="""
<ndc>%s</ndc>""",

    # log4j's 'Mapped Diagnostic Context': additional, customisable information
    # included with the log record
    PROPERTIES="""<properties>%s</properties>""",

    DATA="""
<data name="%s" value="%s"/>""",

    # Exception information, if exc_info was included with the record
    THROWABLE="""
<throwable>%s</throwable>""",

    # Traceback information
    LOCATIONINFO="""
<locationInfo class="%(module)s" method="%(funcName)s" file="%(pathname)s" line="%(lineno)d"/>"""
)

LAYOUT_DEFAULT = LAYOUT_FULL
