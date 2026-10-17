.PHONY: build source deb test test-deb test-native test-webview

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

test-native:
	xvfb-run -a env EWW_NATIVE_TEST_BINARY="$(CURDIR)/build/eww" /usr/bin/python3 -m unittest discover -s tests -p test_native_controls.py -v

test-webview:
	xvfb-run -a env EWW_WEBVIEW_TEST_BINARY="$(CURDIR)/build/eww" /usr/bin/python3 -m unittest discover -s tests -p test_embedded_webview.py -v

.PHONY: test-stacks
test-stacks:
	xvfb-run -a -s '-screen 0 1600x1000x24' /usr/bin/python3 tests/stack-ui-smoke.py
