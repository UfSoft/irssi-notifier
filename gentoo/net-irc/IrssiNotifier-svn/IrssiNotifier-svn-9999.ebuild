# Ebuild for IrssiNotifier from svn
# David Durrleman
# Distributed under the terms of the GNU General Public License v2

inherit distutils eutils subversion

DESCRIPTION="Irssi Real Time Remote Visual Notification."
HOMEPAGE="http://irssinotifier.ufsoft.org/"
ESVN_REPO_URI="http://irssinotifier.ufsoft.org/svn/trunk/"

RDEPEND="dev-python/dbus-python
         dev-python/PyXSS
         dev-python/Babel"
DEPEND="${RDEPEND}
        dev-python/setuptools"

LICENSE="BSD"
SLOT="0"
IUSE=""
KEYWORDS="~x86"

PYTHON_MODNAME="irssinotifier"

src_unpack() {
	subversion_src_unpack
	cd ${S}
	sed -i -e '/install_requires=\[.*\],/d' \
		setup.py || die "sed failed"
}

src_compile() {
	distutils_src_compile
	${python} setup.py compile || die "messages compilation failed"
}

src_install() {
	distutils_src_install
}
