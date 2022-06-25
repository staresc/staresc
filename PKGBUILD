# Maintainer: 5amu <v.casalino@protonmail.com>
pkgname=staresc
pkgver=0
pkgrel=1
_version="v${pkgver}.${pkgrel}"
pkgdesc="Make SSH/TNT PTs Great Again!"
arch=( 'any' )
url="https://github.com/5amu/staresc-ng"
license=( 'GPLv3' )
depends=( 'python' 'python-paramiko' 'python-yaml' 'python-xlsxwriter' )
source=("https://github.com/5amu/staresc-ng/archive/refs/tags/${_version}.tar.gz")
sha256sums=('SKIP')

package() {
	cd "$srcdir/$pkgname-$_version"
	make prefix="$pkgdir" install
}
