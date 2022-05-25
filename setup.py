import sys

from setuptools import setup, find_packages

version = '1.1.1'

extra = {}
#if sys.version_info >= (3,):
#    extra['use_2to3'] = True  # no longer supported by setuptools >= v58.0.0

setup(name='XMLLayout',
      version=version,
      description="Formats Python log messages as log4j XMLLayout XML",
      long_description="""\
XMLLayout provides a Python logging Formatter that formats log messages as XML,
according to `log4j's XMLLayout specification
<https://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/xml/XMLLayout.html>`_.

XMLLayout formatted log messages can be viewed and filtered within the
`Chainsaw <https://logging.apache.org/chainsaw/2.x>`_ application
(see the example section below), part of the Java based log4j project.

This package also includes a RawSocketHandler -- like
logging.handler.SocketHandler, but sends the raw log message over the socket
instead of a pickled version. RawSocketHandler can be configured to send log
messages to Chainsaw directly over a socket.

For example: to forward log messages to Chainsaw, if it were listening on
localhost port 4448::

    import logging
    import xmllayout

    handler = xmllayout.RawSocketHandler('localhost', 4448)
    handler.setFormatter(xmllayout.XMLLayout())
    logging.root.addHandler(handler)
""",
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: Jython',
        'Topic :: System :: Logging'
        ],
      keywords='logging log4j',
      author='Philip Jenvey',
      author_email='pjenvey@underboss.org',
      url='http://pypi.python.org/pypi/XMLLayout',
      license='BSD',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose', 'six'],
      **extra
      )
