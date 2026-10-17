.PHONY: build source deb test test-deb

build:
	./scripts/build-eww.sh

source:
	/usr/bin/python3 scripts/prepare-release-source.py

deb: build source
	/usr/bin/python3 scripts/build-deb.py
	cd dist && sha256sum *.deb *-source.tar.xz > SHA256SUMS

test:
	/usr/bin/python3 -m unittest discover -s tests -v
	/usr/bin/python3 scripts/check_public.py
	git diff --check

test-deb:
	docker run --rm --mount type=bind,src="$(CURDIR)",dst=/package,readonly ubuntu:22.04 /bin/bash /package/tests/deb-smoke.sh /package/dist/ubuntu-widget_$(shell cat VERSION)-1_amd64.deb
