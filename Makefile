pkgname := staresc

requirements:
	python3 -m pip install -r requirements.txt

requirements-arch:
	pacman -S python-paramiko --noconfirm --needed

update:
	git pull --ff-only origin master

install:
	mkdir -p ${prefix}/opt/${pkgname}/{lib,plugins}
	cp -r lib/* ${prefix}/opt/${pkgname}/lib
	cp -r plugins/* ${prefix}/opt/${pkgname}/plugins
	install -Dm644 ./${pkgname}.py ${prefix}/opt/${pkgname}/${pkgname}.py
	install -Dm755 ./${pkgname}.sh ${prefix}/usr/bin/${pkgname}

uninstall:
	rm -rf ${prefix}/opt/${pkgname}
	rm -f  ${prefix}/usr/bin/${pkgname}

publish:
	git clone ssh://aur@aur.archlinux.org/staresc.git aur
	cp PKGBUILD aur/PKGBUILD
	cd aur
	makepkg --printsrcinfo > aur/.SRCINFO
	git --git-dir=aur/.git --work-tree=aur add .
	git --git-dir=aur/.git --work-tree=aur commit "New version"
	git --git-dir=aur/.git --work-tree=aur push origin master

test:
	docker-compose --file ./test/docker-compose.yaml up -d --build
	# Run tests python3 ./test/run.py
	docker-compose --file ./test/docker-compose.yaml down

clean:
	rm -rf pkg src *tar.gz *zst aur

upgrade: uninstall update install
