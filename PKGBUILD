# Maintainer: Mahmut Dikcizgi <boogiepop a~t gmx com>

_name=livearchive
pkgname="${_name}-git"
pkgver=0.1.2
pkgrel=1
pkgdesc='Daemon that binds internet archives like archive.org or theye.eu to virtual FS'
arch=('any')
url="https://github.com/hbiyik/${_name}"
depends=('python-fuse' 'python-lxml' 'python-slugify' 'python-requests')
makedepends=('python-setuptools' 'python-build' 'python-installer' 'python-wheel' 'git')
source=("${pkgname}::git+${url}")
sha256sums=('SKIP')

pkgver(){
  cd "$pkgname"
  _rev=$(git rev-list --count HEAD)
  cd "$_name"
  _ver=$(python -c "from defs import version ; print(version)")
  printf "${_ver}.${_rev}"
}

build() {
  cd "$pkgname"
  python -m build --wheel --no-isolation
}

package() {
  cd "$pkgname"
  install -Dm644 -t "${pkgdir}/usr/lib/systemd/user" "systemd/${_name}.service"
  python -m installer --destdir="$pkgdir" dist/*.whl
}
