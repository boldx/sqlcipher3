# -*- coding: ISO-8859-1 -*-
# setup.py: the distutils script
#
import os
import setuptools
import sys

from distutils import log
from distutils.command.build_ext import build_ext
from setuptools import Extension

# If you need to change anything, it should be enough to change setup.cfg.

PACKAGE_NAME = 'sqlcipher3'
VERSION = '0.1.0'

# define sqlite sources
sources = [os.path.join('src', source)
           for source in ["module.c", "connection.c", "cursor.c", "cache.c",
                          "microprotocols.c", "prepare_protocol.c",
                          "statement.c", "util.c", "row.c"]]

# define packages
packages = [PACKAGE_NAME]
EXTENSION_MODULE_NAME = "._sqlite3"

# Work around clang raising hard error for unused arguments
if sys.platform == "darwin":
    os.environ['CFLAGS'] = "-Qunused-arguments"
    log.info("CFLAGS: " + os.environ['CFLAGS'])


def quote_argument(arg):
    quote = '"' if sys.platform != 'win32' else '\\"'
    return quote + arg + quote

define_macros = [('MODULE_NAME', quote_argument(PACKAGE_NAME + '.dbapi2'))]


class SystemLibSqliteBuilder(build_ext):
    description = "Builds a C extension linking against libsqlcipher library"

    def build_extension(self, ext):
        log.info(self.description)
        build_ext.build_extension(self, ext)


class AmalgationLibSqliteBuilder(build_ext):
    description = "Builds a C extension using a sqlcipher amalgamation"

    amalgamation_root = "."
    amalgamation_header = os.path.join(amalgamation_root, 'sqlite3.h')
    amalgamation_source = os.path.join(amalgamation_root, 'sqlite3.c')

    amalgamation_message = ('Sqlcipher amalgamation not found. Please download'
                            ' or build the amalgamation and make sure the '
                            'following files are present in the sqlcipher3 '
                            'folder: sqlite3.h, sqlite3.c')

    def check_amalgamation(self):
        if not os.path.exists(self.amalgamation_root):
            os.mkdir(self.amalgamation_root)

        header_exists = os.path.exists(self.amalgamation_header)
        source_exists = os.path.exists(self.amalgamation_source)
        if not header_exists or not source_exists:
            raise RuntimeError(self.amalgamation_message)

    def build_extension(self, ext):
        log.info(self.description)

        # it is responsibility of user to provide amalgamation
        self.check_amalgamation()

        ext.define_macros.append(("PYSQLITE_AMALGATION_BUILD", None))

        # Feature-ful library.
        features = (
            'ENABLE_FTS3',
            'ENABLE_FTS3_PARENTHESIS',
            'ENABLE_FTS4',
            'ENABLE_FTS5',
            'ENABLE_JSON1',
            'ENABLE_LOAD_EXTENSION',
            'ENABLE_RTREE',
            'ENABLE_STAT4',
            'ENABLE_UPDATE_DELETE_LIMIT',
            'HAS_CODEC',  # Required for SQLCipher.
            'SOUNDEX',
            'USE_URI',
        )
        for feature in features:
            ext.define_macros.append(('SQLITE_%s' % feature, '1'))

        # Required for SQLCipher.
        ext.define_macros.append(("SQLITE_TEMP_STORE", "2"))

        # Additional nice-to-have.
        ext.define_macros.extend((
            ('SQLITE_DEFAULT_PAGE_SIZE', '4096'),
            ('SQLITE_DEFAULT_CACHE_SIZE', '-8000')))  # 8MB.

        ext.include_dirs.append(self.amalgamation_root)
        ext.sources.append(os.path.join(self.amalgamation_root, "sqlite3.c"))

        if sys.platform != "win32":
            # Include math library, required for fts5, and crypto.
            ext.extra_link_args.extend(["-lm", "-lcrypto"])
        else:
            # Try to locate openssl.
            openssl_conf = os.environ.get('OPENSSL_CONF')
            if not openssl_conf:
                error_message = 'Fatal error: OpenSSL could not be detected!'
                raise RuntimeError(error_message)

            openssl = os.path.dirname(os.path.dirname(openssl_conf))
            openssl_lib_path = os.path.join(openssl, "lib")

            # Configure the compiler
            ext.include_dirs.append(os.path.join(openssl, "include"))
            ext.define_macros.append(("inline", "__inline"))

            # Configure the linker
            ext.extra_link_args.append("libeay32.lib")
            ext.extra_link_args.append('/LIBPATH:' + openssl_lib_path)

        build_ext.build_extension(self, ext)

    def __setattr__(self, k, v):
        # Make sure we don't link against the SQLite
        # library, no matter what setup.cfg says
        if k == "libraries":
            v = None
        self.__dict__[k] = v


def get_setup_args():
    return dict(
        name=PACKAGE_NAME,
        version=VERSION,
        description="DB-API 2.0 interface for SQLCipher 3.x",
        long_description='',
        author="Charles Leifer",
        author_email="coleifer@gmail.com",
        license="zlib/libpng",
        platforms="ALL",
        url="https://github.com/coleifer/sqlcipher3",
        package_dir={PACKAGE_NAME: "lib"},
        packages=packages,
        ext_modules=[Extension(
            name=PACKAGE_NAME + EXTENSION_MODULE_NAME,
            sources=sources,
            define_macros=define_macros)
        ],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: zlib/libpng License",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX",
            "Programming Language :: C",
            "Programming Language :: Python",
            "Topic :: Database :: Database Engines/Servers",
            "Topic :: Software Development :: Libraries :: Python Modules"],
        cmdclass={
            "build_static": AmalgationLibSqliteBuilder,
            "build_ext": SystemLibSqliteBuilder
        }
    )


def main():
    try:
        setuptools.setup(**get_setup_args())
    except BaseException as ex:
        log.info(str(ex))

if __name__ == "__main__":
    main()
