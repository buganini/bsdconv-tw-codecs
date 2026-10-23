PREFIX?=/usr/local
CODECS=
CODECS+=inter/TW-JUDICIAL-PUA-XP
CODECS+=inter/TW-JUDICIAL-PUA-UNICODE

all: builddir codecs

builddir:
	mkdir -p build/share/bsdconv/from
	mkdir -p build/share/bsdconv/inter
	mkdir -p build/share/bsdconv/to

codecs: builddir
	@for item in ${CODECS} ; do \
		bsdconv-mktable modules/$${item}.txt ./build/share/bsdconv/$${item} ; \
		if [ -e modules/$${item}.c ]; then $(CC) ${CFLAGS} modules/$${item}.c -L./build/lib/ -fPIC -shared -o ./build/share/bsdconv/$${item}.so -lbsdconv ${LIBS} ; fi ; \
	done

clean:
	rm -rf build

installdir:
	mkdir -p ${PREFIX}/share/bsdconv/from
	mkdir -p ${PREFIX}/share/bsdconv/inter
	mkdir -p ${PREFIX}/share/bsdconv/to

install: installdir
	@for item in ${CODECS} ; do \
		install -m 444 build/share/bsdconv/$${item} ${PREFIX}/share/bsdconv/$${item} ; \
		if [ -e build/share/bsdconv/$${item}.so ]; then install -m 444 build/share/bsdconv/$${item}.so ${PREFIX}/share/bsdconv/$${item}.so ; fi ; \
	done

TW_JUDICIAL_PUA_XP=https://jfont.judicial.gov.tw/jfont/jfontXP.exe
TW_JUDICIAL_PUA_UNICODE=https://jfont.judicial.gov.tw/jfont/jfontEUDC.exe

.PHONY: gen gen_judical_pua_xp gen_judical_pua_unicode
gen: gen_judical_pua_xp gen_judical_pua_unicode

gen_judical_pua_xp: PUA_SOURCE=${TW_JUDICIAL_PUA_XP}
gen_judical_pua_xp: PUA_FORMAT=xp
gen_judical_pua_xp: PUA_CODEC=TW-JUDICIAL-PUA-XP

gen_judical_pua_unicode: PUA_SOURCE=${TW_JUDICIAL_PUA_UNICODE}
gen_judical_pua_unicode: PUA_FORMAT=unicode
gen_judical_pua_unicode: PUA_CODEC=TW-JUDICIAL-PUA-UNICODE

gen_judical_pua_xp gen_judical_pua_unicode:
	@set -eu; \
	workdir=$$(mktemp -d ./tw-judicial-pua.XXXXXX); \
	trap 'rm -rf "$$workdir"' 0; \
	wget -O "$$workdir/jfont.exe" "${PUA_SOURCE}"; \
	bsdtar -xf "$$workdir/jfont.exe" -C "$$workdir" '造字對照表.pdf'; \
	pdftotext -layout -enc UTF-8 "$$workdir/造字對照表.pdf" "$$workdir/table.txt"; \
	python3 tools/tw-judicial-pua.py --format "${PUA_FORMAT}" "$$workdir/table.txt" > "$$workdir/mappings.txt"; \
	printf '#Source: %s\n' "${PUA_SOURCE}" > "$$workdir/output.txt"; \
	cat "$$workdir/mappings.txt" >> "$$workdir/output.txt"; \
	mv "$$workdir/output.txt" "modules/inter/${PUA_CODEC}.txt"
