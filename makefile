script := presentation.py
app    := Presentation.app

.PHONY: all clean

all: $(app)

$(app): $(script)
	mkdir -p $@/Contents/MacOS/
	echo "APPL????" > $@/Contents/PkgInfo
	echo "\
	<?xml version='1.0' encoding='UTF-8'?> \
	<!DOCTYPE plist PUBLIC '-//Apple//DTD PLIST 1.0//EN' 'http://www.apple.com/DTDs/PropertyList-1.0.dtd'> \
	<plist version='1.0'> \
	<dict><key>CFBundleExecutable</key><string>$^</string></dict> \
	</plist>" > $@/Contents/Info.plist
	
	cp $^ $@/Contents/MacOS/
	touch $@

clean:
	-rm -rf $(app)
