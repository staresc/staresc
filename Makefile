pkgname := staresc

modulename := staresc

requirements:
	python3 -m pip install -r requirements.txt

update:
	git pull --ff-only origin main

install:
	mkdir -p "${prefix}/opt/${pkgname}/${modulename}"
	mkdir -p "${prefix}/opt/${pkgname}/plugins"
	mkdir -p "${prefix}/usr/bin"

	cp -r "${modulename}"/* "${prefix}/opt/${pkgname}/${modulename}"
	cp -r "plugins/"* "${prefix}/opt/${pkgname}/plugins"
	install -Dm644 "./${pkgname}.py" "${prefix}/opt/${pkgname}/${pkgname}.py"

	echo '#!/bin/sh\n/usr/bin/python3 /opt/${pkgname}/${pkgname}.py $$@' > "${prefix}/usr/bin/${pkgname}"
	chmod 755 "${prefix}/usr/bin/${pkgname}"

uninstall:
	rm -rf ${prefix}/opt/${pkgname}
	rm -f  ${prefix}/usr/bin/${pkgname}

clean:
	rm -rf pkg src *tar.gz *zst aur

upgrade: uninstall update install
