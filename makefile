# variables ##################################################################

DIST_PATH = release

version = $(shell ./presentation.py --version)
VERSION = $(lastword $(version))
IDENTIFIER = $(word 2,$(version))


# targets ####################################################################

script  := presentation.py
icon    := presentation.icns
iconset := presentation.iconset
app     := Présentation.app
dist    := osx-presentation-$(VERSION).pkg
src     := osx-presentation-$(VERSION).tbz


# rules ######################################################################

.PHONY: all clean pkg archive

all: $(app)

$(app): $(script) $(icon) makefile
	mkdir -p $@/Contents/
	echo "APPL????" > $@/Contents/PkgInfo
	echo "\
	<?xml version='1.0' encoding='UTF-8'?> \
	<!DOCTYPE plist PUBLIC '-//Apple//DTD PLIST 1.0//EN' 'http://www.apple.com/DTDs/PropertyList-1.0.dtd'> \
	<plist version='1.0'> \
	<dict> \
		<key>CFBundleExecutable</key><string>$<</string> \
		<key>CFBundleIdentifier</key><string>$(IDENTIFIER)</string> \
		<key>CFBundleDocumentTypes</key><array><dict> \
			<key>CFBundleTypeName</key><string>Adobe PDF document</string> \
			<key>LSItemContentTypes</key><array> \
				<string>com.adobe.pdf</string> \
			</array> \
			<key>CFBundleTypeRole</key><string>Viewer</string> \
			<key>LSHandlerRank</key><string>Alternate</string> \
		</dict></array> \
		<key>CFBundleShortVersionString</key><string>$(VERSION)</string> \
		<key>NSHumanReadableCopyright</key><string>Copyright © 2011-2020 Renaud Blanch</string> \
		<key>CFBundleIconFile</key><string>presentation</string> \
	</dict> \
	</plist>" > $@/Contents/Info.plist
	
	mkdir -p $@/Contents/MacOS/
	cp $< $@/Contents/MacOS/
	
	mkdir -p $@/Contents/Resources/
	cp $(icon) $@/Contents/Resources/
	
	touch $@

$(icon): $(iconset)
	iconutil --convert icns --output $@ $<

$(iconset): $(script)
	mkdir -p $@
	./$< --icon > $@/icon_256x256.png

archive:
	hg archive -r $(VERSION) -t tbz2 $@

pkg: $(app) $(dist)

$(dist): $(app)
	mkdir $(DIST_PATH)
	cp -r $^ $(DIST_PATH)
	pkgbuild --root $(DIST_PATH) --identifier $(IDENTIFIER) --version $(VERSION) --install-location /Applications $@
	rm -rf $(DIST_PATH)


clean:
	-rm -rf $(app) $(src) $(dist) $(icon) $(iconset)
