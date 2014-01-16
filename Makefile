PREFIX?=/usr/local
CODECS=
CODECS+=inter/TW-JUDICIAL-PUA

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

TW_JUDICIAL_PUA=http://www.judicial.gov.tw/jfont/%E9%80%A0%E5%AD%97%E5%B0%8D%E7%85%A7%E8%A1%A8.pdf
gen:
	#TW_JUDICIAL_PUA
	wget -O /tmp/TW_JUDICIAL_PUA.pdf ${TW_JUDICIAL_PUA}
	pdftotext /tmp/TW_JUDICIAL_PUA.pdf
	echo "#Source:" ${TW_JUDICIAL_PUA} > modules/inter/TW-JUDICIAL-PUA.txt
	python tools/tw-judicial-pua.py /tmp/TW_JUDICIAL_PUA.txt | sort >> modules/inter/TW-JUDICIAL-PUA.txt
	rm -rf /tmp/TW_JUDICIAL_PUA.pdf /tmp/TW_JUDICIAL_PUA.txt
