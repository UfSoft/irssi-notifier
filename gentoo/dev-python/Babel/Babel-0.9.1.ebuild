# Ebuild for Babel
# David Durrleman
# Distributed under the terms of the GNU General Public License v2

inherit distutils

DESCRIPTION="A collection of tools for internationalizing Python applications"
HOMEPAGE="http://babel.edgewall.org/"
SRC_URI="http://ftp.edgewall.com/pub/babel/${P}.tar.bz2"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86"
IUSE=""

RDEPEND="dev-python/pytz >=dev-lang/python-2.3"
DEPEND="${RDEPEND}"
