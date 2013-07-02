# variables ##################################################################

DMG_PATH = dmg
VERSION = $(lastword $(shell ./presentation.py --version))


# targets ####################################################################

script := presentation.py
app    := Présentation.app
dist   := osx-presentation-$(VERSION).dmg
src    := osx-presentation-$(VERSION).tbz
readme := README.rst


# rules ######################################################################

.PHONY: all clean dmg archive

all: $(app)

$(app): $(script)
	mkdir -p $@/Contents/MacOS/
	echo "APPL????" > $@/Contents/PkgInfo
	echo "\
	<?xml version='1.0' encoding='UTF-8'?> \
	<!DOCTYPE plist PUBLIC '-//Apple//DTD PLIST 1.0//EN' 'http://www.apple.com/DTDs/PropertyList-1.0.dtd'> \
	<plist version='1.0'> \
	<dict> \
		<key>CFBundleExecutable</key><string>$^</string> \
		<key>CFBundleShortVersionString</key><string>$(VERSION).0</string> \
		<key>NSHumanReadableCopyright</key><string>Copyright © 2011-2013 Renaud Blanch</string> \
	</dict> \
	</plist>" > $@/Contents/Info.plist
	
	cp $^ $@/Contents/MacOS/
	touch $@


archive:
	hg archive -r $(VERSION) -t tbz2 $@

dmg: $(app) $(dist)

$(dist): $(app) $(readme)
	mkdir $(DMG_PATH)
	cp -r $^ $(DMG_PATH)
	hdiutil create -ov -srcfolder $(DMG_PATH) -volname $(basename $@) $@
	hdiutil internet-enable -yes $@
	rm -rf $(DMG_PATH)


clean:
	-rm -rf $(app) $(src) $(dist)
