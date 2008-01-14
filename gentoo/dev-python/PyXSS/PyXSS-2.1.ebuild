# Ebuild for PyXSS
# David Durrleman
# Distributed under the terms of the GNU General Public License v2

inherit distutils

DESCRIPTION="Provides a python interface for querying X Screensaver"
HOMEPAGE="http://bebop.bigasterisk.com/python/"
SRC_URI="http://www.pioto.org/~pioto/gentoo/distfiles/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86"
IUSE=""

RDEPEND=">=dev-lang/python-2.2"
