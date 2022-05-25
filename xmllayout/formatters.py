"""logging Formatters"""
try:
    from cgi import escape # < Python3.7
except ImportError:
    from html import escape
import logging
import re

__all__ = ['XMLLayout']

# Level names differ slightly in log4j, see
# http://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/Level.html
LOG4J_LEVELS = dict(WARNING='WARN', CRITICAL='FATAL')


class XMLLayout(logging.Formatter):

    """Formats log Records as XML according to the `log4j XMLLayout
    <http://logging.apache.org/log4j/docs/api/org/apache/log4j/xml/
    XMLLayout.html>_`
    """

    NDC_ATTRIBUTE = 'ndc'
    MDC_RE = re.compile('mdc:(?P<name>.*)')

    def format(self, record):
        """Format the log record as XMLLayout XML"""
        levelname = LOG4J_LEVELS.get(record.levelname, record.levelname)
        event = dict(name=escape(record.name),
                     threadName=escape(record.threadName),
                     levelname=escape(levelname),
                     created=int(record.created * 1000))

        event['message'] = LOG4J_MESSAGE % escape_cdata(record.getMessage())

        event['ndc'] = ''
        ndc = self.get_ndc(record)
        if ndc:
            event['ndc'] = LOG4J_NDC % escape_cdata(ndc)

        # MDC data is stored within a <log4j:properties> element
        event['properties'] = ''
        mdc = self.get_mdc(record)
        if mdc:
            keys = list(mdc.keys())
            keys.sort()
            data = "".join(LOG4J_DATA % (escape(k), escape(mdc[k])) for k in keys)
            event['properties'] = LOG4J_PROPERTIES % data

        event['throwable'] = ''
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            event['throwable'] = (LOG4J_THROWABLE %
                                  escape_cdata(record.exc_text))

        location_info = dict(pathname=escape(record.pathname),
                             lineno=record.lineno,
                             module=escape(record.module), funcName='')
        if hasattr(record, 'funcName'):
            # >= Python 2.5
            location_info['funcName'] = escape(record.funcName)
        event['locationInfo'] = LOG4J_LOCATIONINFO % location_info

        return LOG4J_EVENT % event


    def get_ndc(self, record):
        try:
            if self.NDC_ATTRIBUTE:
                return getattr(record, self.NDC_ATTRIBUTE)
        except Exception:
            pass
        return ''

    def get_mdc(self, record):
        mdc = {}
        for k in dir(record):
            match = self.MDC_RE.match(k)
            if match is not None:
                try:
                    mdc[match.group('name')] = getattr(record, k)
                except Exception:
                    pass
        return mdc

def escape_cdata(cdata):
    """Escape XML CDATA content"""
    return cdata.replace(']]>', ']]]]><![CDATA[>')

# General logging information
LOG4J_EVENT = """\
<log4j:event logger="%(name)s"
    timestamp="%(created)i"
    level="%(levelname)s"
    thread="%(threadName)s">
%(message)s%(ndc)s%(throwable)s%(locationInfo)s%(properties)s</log4j:event>
"""

# The actual log message
LOG4J_MESSAGE = """\
    <log4j:message><![CDATA[%s]]></log4j:message>
"""

# log4j's 'Nested Diagnostic Context': additional, customizable information
# included with the log record
LOG4J_NDC = """\
    <log4j:ndc><![CDATA[%s]]></log4j:ndc>
"""

# log4j's 'Mapped Diagnostic Context': additional, customizable information
# included with the log record
LOG4J_PROPERTIES = """\
    <log4j:properties>
%s    </log4j:properties>
"""

LOG4J_DATA = """\
      <log4j:data name="%s" value="%s"/>
"""

# Exception information, if exc_info was included with the record
LOG4J_THROWABLE = """\
    <log4j:throwable><![CDATA[%s]]></log4j:throwable>
"""

# Traceback information
LOG4J_LOCATIONINFO = """\
    <log4j:locationInfo class="%(module)s"
        method="%(funcName)s"
        file="%(pathname)s"
        line="%(lineno)d"/>
"""
