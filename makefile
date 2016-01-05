# variables ##################################################################

DMG_PATH = dmg
VERSION = $(lastword $(shell ./presentation.py --version))


# targets ####################################################################

script  := presentation.py
icon    := presentation.icns
iconset := presentation.iconset
app     := Présentation.app
dist    := osx-presentation-$(VERSION).dmg
src     := osx-presentation-$(VERSION).tbz


# rules ######################################################################

.PHONY: all clean dmg archive

all: $(app)

$(app): $(script) $(icon)
	mkdir -p $@/Contents/
	echo "APPL????" > $@/Contents/PkgInfo
	echo "\
	<?xml version='1.0' encoding='UTF-8'?> \
	<!DOCTYPE plist PUBLIC '-//Apple//DTD PLIST 1.0//EN' 'http://www.apple.com/DTDs/PropertyList-1.0.dtd'> \
	<plist version='1.0'> \
	<dict> \
		<key>CFBundleExecutable</key><string>$<</string> \
		<key>CFBundleDocumentTypes</key><array><dict> \
			<key>CFBundleTypeName</key><string>Adobe PDF document</string> \
			<key>LSItemContentTypes</key><array> \
				<string>com.adobe.pdf</string> \
			</array> \
			<key>CFBundleTypeRole</key><string>Viewer</string> \
			<key>LSHandlerRank</key><string>Alternate</string> \
		</dict></array> \
		<key>CFBundleShortVersionString</key><string>$(VERSION).0</string> \
		<key>NSHumanReadableCopyright</key><string>Copyright © 2011-2016 Renaud Blanch</string> \
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

dmg: $(app) $(dist)

$(dist): $(app)
	mkdir $(DMG_PATH)
	ln -s /Applications $(DMG_PATH)/
	cp -r $^ $(DMG_PATH)
	hdiutil create -ov -srcfolder $(DMG_PATH) -volname $(basename $@) $@
	hdiutil internet-enable -yes $@
	rm -rf $(DMG_PATH)


clean:
	-rm -rf $(app) $(src) $(dist) $(icon) $(iconset)
