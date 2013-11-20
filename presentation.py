#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""
A PDF presentation tool for Mac OS X

Copyright (c) 2011--2013, IIHM/LIG - Renaud Blanch <http://iihm.imag.fr/blanch/>
Licence: GPLv3 or higher <http://www.gnu.org/licenses/gpl.html>
"""


# imports ####################################################################

import sys
import os
import time
import select
import getopt
import textwrap
import mimetypes

from math import exp
from collections import defaultdict


# constants and helpers ######################################################

NAME = "Présentation"
MAJOR, MINOR = 0, 9
VERSION = "%s.%s" % (MAJOR, MINOR)
HOME = "http://iihm.imag.fr/blanch/software/osx-presentation/"
CREDITS = """
<a href='%s'>osx-presentation</a> <br/>
Licence: <a href='http://www.gnu.org/licenses/gpl-3.0.txt'>GPLv3</a>+
""" % HOME
COPYRIGHT = "Copyright © 2011-2013 Renaud Blanch"
ICON = "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"

PRESENTER_FRAME   = ((100., 100.), (1024., 768.))
MIN_POSTER_HEIGHT = 20.

HELP = [
	("?",       "show/hide this help"),
	("h",       "hide"),
	("q",       "quit"),
	("w",       "toggle web view"),
	("m",       "toggle movie view"),
	("s",       "show slide view"),
	("f",       "toggle fullscreen"),
	("⎋",       "leave fullscreen"),
	("←/↑",     "previous page"),
	("→/↓",     "next page"),
	("⇞",       "back"),
	("⇟",       "forward"),
	("↖",       "first page"),
	("↘",       "last page"),
	("t/space", "start/stop timer"),
	("z",       "set origin for timer"),
	("[/]",     "sub/add  1 minute to planned time"),
	("{/}",     "sub/add 10 minutes"),
	("+/-/0",   "zoom in/out/reset web view"),
]

def nop(): pass


# handling args ##############################################################

name, args = sys.argv[0], sys.argv[1:]

# ignore "-psn" arg if we have been launched by the finder
launched_from_finder = args and args[0].startswith("-psn")
if launched_from_finder:
	args = args[1:]


def exit_usage(message=None, code=0):
	usage = textwrap.dedent("""\
	Usage: %s [-hvid:f] <doc.pdf>
		-h --help          print this help message then exit
		-v --version       print version then exit
		-i --icon          print icon then exit
		-d --duration <t>  duration of the talk in minutes
		-f --feed          enable reading feed on stdin
		<doc.pdf>          file to present
	""" % name)
	if message:
		sys.stderr.write("%s\n" % message)
	sys.stderr.write(usage)
	sys.exit(code)

def exit_version():
	sys.stdout.write("%s %s\n" % (os.path.basename(name), VERSION))
	sys.exit()

def exit_icon():
	import base64
	sys.stdout.write(base64.b64decode(ICON))
	sys.exit()


# options

try:
	options, args = getopt.getopt(args, "hvid:f", ["help", "version", "icon",
	                                               "duration=", "feed"])
except getopt.GetoptError as message:
	exit_usage(message, 1)

show_feed = False
presentation_duration = 0

for opt, value in options:
	if opt in ["-h", "--help"]:
		exit_usage()
	elif opt in ["-v", "--version"]:
		exit_version()
	elif opt in ["-i", "--icon"]:
		exit_icon()
	elif opt in ["-d", "--duration"]:
		presentation_duration = int(value)
	elif opt in ["-f", "--feed"]:
		show_feed = True

if len(args) > 1:
	exit_usage("no more than one argument is expected", 1)


# application init ###########################################################

from objc import setVerbose
setVerbose(1)

from objc import nil, NO, YES
from Foundation import (
	NSLog, NSNotificationCenter,
	NSObject, NSTimer, NSError, NSString, NSData,
	NSAttributedString, NSUnicodeStringEncoding,
	NSURL, NSURLRequest, NSURLConnection,
	NSAffineTransform,
)

from AppKit import (
	NSApplication,
	NSApplicationDidFinishLaunchingNotification,
	NSOpenPanel, NSFileHandlingPanelOKButton,
	NSAlert, NSAlertDefaultReturn,
	NSView,
	NSViewWidthSizable, NSViewHeightSizable,
	NSWindow,
	NSMiniaturizableWindowMask, NSResizableWindowMask, NSTitledWindowMask,
	NSBackingStoreBuffered,
	NSCommandKeyMask, NSAlternateKeyMask,
	NSMenu, NSMenuItem,
	NSGraphicsContext,
	NSCompositeClear, NSCompositeSourceAtop, NSCompositeCopy,
	NSRectFillUsingOperation, NSFrameRectWithWidth, NSFrameRect, NSEraseRect,
	NSZeroRect,
	NSColor, NSCursor, NSFont,
	NSFontAttributeName,	NSForegroundColorAttributeName,
	NSStrokeColorAttributeName, NSStrokeWidthAttributeName,
	NSUpArrowFunctionKey, NSLeftArrowFunctionKey,
	NSDownArrowFunctionKey, NSRightArrowFunctionKey,
	NSHomeFunctionKey, NSEndFunctionKey,
	NSPageUpFunctionKey, NSPageDownFunctionKey,
	NSScreen, NSWorkspace, NSImage,
)

from Quartz import (
	PDFDocument, PDFAnnotationText, PDFAnnotationLink,
	PDFActionNamed,
	kPDFActionNamedNextPage, kPDFActionNamedPreviousPage,
	kPDFActionNamedFirstPage, kPDFActionNamedLastPage,
	kPDFActionNamedGoBack, kPDFActionNamedGoForward,
	kPDFDisplayBoxCropBox,
)

from WebKit import (
	WebView,
)

from QTKit import (
	QTMovie, QTMovieView,
)

# QTKit is deprecated in 10.9 but AVFoundation will only be in PyObjC-3.0+
# so wait and see, and remember for future reference:
# https://developer.apple.com/library/mac/technotes/tn2300/_index.html


if sys.version_info[0] == 3:
	_s = NSString.stringWithString_
	sys.stdin = sys.stdin.detach() # so that sys.stdin.readline returns bytes
else:
	_s = NSString.alloc().initWithUTF8String_

def _h(s):
	h, _ = NSAttributedString.alloc().initWithHTML_documentAttributes_(
		_s(s).dataUsingEncoding_(NSUnicodeStringEncoding), None)
	return h

ICON = NSImage.alloc().initWithData_(NSData.alloc().initWithBase64Encoding_(ICON))

app = NSApplication.sharedApplication()
app.activateIgnoringOtherApps_(True)

if launched_from_finder:
	# HACK: run application to get dropped filename if any and then stop it
	class DropApplicationDelegate(NSObject):
		def application_openFile_(self, app, filename):
			filename = filename.encode("utf-8")
			if filename != os.path.abspath(__file__):
				args.append(filename)
		def applicationDidFinishLaunching_(self, notification):
			app.stop_(self)
	application_delegate = DropApplicationDelegate.alloc().init()
	app.setDelegate_(application_delegate)
	app.run()


if args:
	url = NSURL.fileURLWithPath_(args[0])
else:
	dialog = NSOpenPanel.openPanel()
	dialog.setAllowedFileTypes_(["pdf"])
	if dialog.runModal() == NSFileHandlingPanelOKButton:
		url, = dialog.URLs()
	else:
		exit_usage("please select a pdf file", 1)


# opening presentation

file_name = url.lastPathComponent()
pdf = PDFDocument.alloc().initWithURL_(url)
if not pdf:
	exit_usage("'%s' does not seem to be a pdf." % url.path(), 1)


# page navigation

page_count = pdf.pageCount()
first_page, last_page = 0, page_count-1

past_pages = []
current_page = first_page
future_pages = []

def _goto(page):
	global current_page
	current_page = page
	presentation_show(slide_view)

def _pop_push_page(pop_pages, push_pages):
	def action():
		try:
			page = pop_pages.pop()
		except IndexError:
			return
		push_pages.append(current_page)
		_goto(page)
	return action


back    = _pop_push_page(past_pages, future_pages)
forward = _pop_push_page(future_pages, past_pages)

def goto_page(page):
	page = min(max(first_page, page), last_page)
	if page == current_page:
		return
	
	if future_pages and page == future_pages[-1]:
		forward()
	elif past_pages and page == past_pages[-1]:
		back()
	else:
		del future_pages[:]
		past_pages.append(current_page)
		_goto(page)


def next_page(): goto_page(current_page+1)
def prev_page(): goto_page(current_page-1)
def home_page(): goto_page(first_page)
def end_page():  goto_page(last_page)


# annotations

def get_movie(url):
	"""return a QTMovie object from an url if possible/desirable"""
	if not (url and url.scheme() == "file"):
		return
	mimetype, _ = mimetypes.guess_type(url.absoluteString())
	if not (mimetype and mimetype.startswith("video")):
		return
	if not QTMovie.canInitWithURL_(url):
		return
	movie, error = QTMovie.movieWithURL_error_(url, None)
	if error:
		return
	return movie

notes  = defaultdict(list)
movies = {}
for page_number in range(page_count):
	page = pdf.pageAtIndex_(page_number)
	page.setDisplaysAnnotations_(False)
	for annotation in page.annotations():
		annotation_type = type(annotation)
		if annotation_type == PDFAnnotationText:
			notes[page_number].append(annotation.contents())
		elif annotation_type == PDFAnnotationLink:
			movie = get_movie(annotation.URL())
			if movie:
				movies[annotation] = (movie, movie.posterImage())


# page drawing ###############################################################

bbox = NSAffineTransform.transform()

def draw_page(page):
	bbox.concat()

	NSEraseRect(page.boundsForBox_(kPDFDisplayBoxCropBox))
	page.drawWithBox_(kPDFDisplayBoxCropBox)
	
	NSColor.blackColor().setFill()
	for annotation in page.annotations():
		if not annotation in movies:
			continue
		bounds = annotation.bounds()

		_, poster = movies[annotation]
		if poster is None:
			continue
		
		bounds_size = bounds.size
		if bounds_size.height < MIN_POSTER_HEIGHT:
			continue
		
		NSRectFillUsingOperation(bounds, NSCompositeCopy)
		
		poster_size = poster.size()
		aspect_ratio = ((poster_size.width*bounds_size.height)/
		                (bounds_size.width*poster_size.height))
		if aspect_ratio < 1:
			dw = bounds.size.width * (1.-aspect_ratio)
			bounds.origin.x += dw/2.
			bounds.size.width -= dw
		else:
			dh = bounds.size.height * (1.-1./aspect_ratio)
			bounds.origin.y += dh/2.
			bounds.size.height -= dh
		
		poster.drawInRect_fromRect_operation_fraction_(
			bounds, NSZeroRect, NSCompositeCopy, 1.
		)


# presentation ###############################################################

class SlideView(NSView):
	def drawRect_(self, rect):
		bounds = self.bounds()
		width, height = bounds.size
		
		NSRectFillUsingOperation(bounds, NSCompositeClear)
		
		# current page
		page = pdf.pageAtIndex_(current_page)
		page_rect = page.boundsForBox_(kPDFDisplayBoxCropBox)
		_, (w, h) = page_rect
		r = min(width/w, height/h)
		
		NSGraphicsContext.saveGraphicsState()
		transform = NSAffineTransform.transform()
		transform.translateXBy_yBy_(width/2., height/2.)
		transform.scaleXBy_yBy_(r, r)
		transform.translateXBy_yBy_(-w/2., -h/2.)
		transform.concat()
		draw_page(page)
		NSGraphicsContext.restoreGraphicsState()


class MessageView(NSView):
	fps = 20. # frame per seconds for animation
	pps = 40. # pixels per seconds for scrolling

	input_lines = [u"…"]
	should_check = True
	
	def initWithFrame_(self, frame):
		assert NSView.initWithFrame_(self, frame) == self
		self.redisplay_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
			1./self.fps,
			self, "redisplay:", nil,
			True
		)
		return self

	def redisplay_(self, timer):
		self.setNeedsDisplay_(True)
	
	def check_input(self):
		while True:
			ready, _, _ = select.select([sys.stdin], [], [], 0)
			if not ready:
				break
			line = sys.stdin.readline().decode('utf-8')
			self.input_lines.append(line.rstrip())
	
	def drawRect_(self, rect):
		if self.should_check:
			self.check_input()
			try:
				self.text = self.input_lines.pop(0)
			except IndexError:
				pass
			else:
				self.start = time.time()
				self.should_check = False
		text = NSString.stringWithString_(self.text)
		x = rect.size.width - self.pps*(time.time()-self.start)
		for attr in [{
			NSFontAttributeName:            NSFont.labelFontOfSize_(30),
			NSStrokeColorAttributeName:     NSColor.colorWithDeviceWhite_alpha_(0., .75),
			NSStrokeWidthAttributeName:     20.,
		}, {
			NSFontAttributeName:            NSFont.labelFontOfSize_(30),
			NSForegroundColorAttributeName: NSColor.colorWithDeviceWhite_alpha_(1., .75),
		}]:
			text.drawAtPoint_withAttributes_((x, 4.), attr)
		tw, _ = text.sizeWithAttributes_(attr)
		if x < -tw:
			self.should_check = True


# presenter view #############################################################

class PresenterView(NSView):
	transform = NSAffineTransform.transform()
	duration = presentation_duration * 60.
	absolute_time = True
	elapsed_duration = 0
	start_time = time.time()
	duration_change_time = 0
	show_help = True
	annotation_state = None
	
	def drawRect_(self, rect):
		bounds = self.bounds()
		width, height = bounds.size

		margin = width / 20.
		current_width = (width-3*margin)*2/3.
		font_size = margin/2.
		
		NSRectFillUsingOperation(bounds, NSCompositeClear)

		# current 
		self.page = pdf.pageAtIndex_(current_page)
		page_rect = self.page.boundsForBox_(kPDFDisplayBoxCropBox)
		_, (w, h) = page_rect
		r = current_width/w
		
		NSGraphicsContext.saveGraphicsState()
		transform = NSAffineTransform.transform()
		transform.translateXBy_yBy_(margin, height-1.5*margin)
		transform.scaleXBy_yBy_(r, r)
		transform.translateXBy_yBy_(0., -h)
		transform.concat()
		
		NSGraphicsContext.saveGraphicsState()
		
		draw_page(self.page)
		
		# links
		NSColor.blueColor().setFill()
		for annotation in self.page.annotations():
			if type(annotation) == PDFAnnotationLink:
				NSFrameRectWithWidth(annotation.bounds(), .5)

		self.transform = transform
		self.transform.prependTransform_(bbox)
		self.resetCursorRects()
		self.transform.invert()

		NSGraphicsContext.restoreGraphicsState()
		
		# screen border
		NSColor.grayColor().setFill()
		NSFrameRect(page_rect)
		NSGraphicsContext.restoreGraphicsState()
		

		# time
		now = time.time()
		if now - self.duration_change_time <= 1: # duration changed, display it
			clock = self.duration
		elif self.absolute_time:
			clock = now
		else:
			runing_duration = now - self.start_time + self.elapsed_duration
			clock = abs(self.duration - runing_duration)
		clock = time.gmtime(clock)
		clock = NSString.stringWithString_(time.strftime("%H:%M:%S", clock))
		clock.drawAtPoint_withAttributes_((margin, height-1.4*margin), {
			NSFontAttributeName:            NSFont.labelFontOfSize_(margin),
			NSForegroundColorAttributeName: NSColor.whiteColor(),
		})
	
		# page number
		page_number = NSString.stringWithString_("%s (%s/%s)" % (
			self.page.label(), current_page+1, page_count))
		attr = {
			NSFontAttributeName:            NSFont.labelFontOfSize_(font_size),
			NSForegroundColorAttributeName: NSColor.whiteColor(),
		}
		tw, _ = page_number.sizeWithAttributes_(attr)
		page_number.drawAtPoint_withAttributes_((margin+current_width-tw,
		                                         height-1.4*margin), attr)

		# notes
		note = NSString.stringWithString_("\n".join(notes[current_page]))
		note.drawAtPoint_withAttributes_((margin, font_size), {
			NSFontAttributeName:            NSFont.labelFontOfSize_(font_size/2.),
			NSForegroundColorAttributeName: NSColor.whiteColor(),
		})
		
		# help
		if self.show_help:
			help_text = _h("".join([
				"<table style='color: white; font-family: LucidaGrande;'>"
			] + [
				"<tr><th style='padding: 0 1em;' align='right'>%s</th><td>%s</td></tr>" % h for h in HELP
			] + [
				"</table>"
			]))
			help_text.drawAtPoint_((2*margin+current_width, font_size))
		
		# next page
		try:
			page = pdf.pageAtIndex_(current_page+1)
		except:
			return
		page_rect = page.boundsForBox_(kPDFDisplayBoxCropBox)
		_, (w, h) = page_rect
		r = current_width/2./w
	
		NSGraphicsContext.saveGraphicsState()
		transform = NSAffineTransform.transform()
		transform.translateXBy_yBy_(2*margin+current_width, height-2.*margin)
		transform.scaleXBy_yBy_(r, r)
		transform.translateXBy_yBy_(0., -h)
		transform.concat()
		bbox.concat()

		NSEraseRect(page_rect)
		page.drawWithBox_(kPDFDisplayBoxCropBox)
		NSColor.colorWithCalibratedWhite_alpha_(.25, .25).setFill()
		NSRectFillUsingOperation(page_rect, NSCompositeSourceAtop)
		NSGraphicsContext.restoreGraphicsState()
	
	
	def resetCursorRects(self):
		# updates rectangles only if needed (so that tooltip timeouts work)
		annotation_state = (self.transform.transformStruct(), current_page)
		if self.annotation_state == annotation_state:
			return
		self.annotation_state = annotation_state
		
		# reset cursor rects and tooltips
		self.discardCursorRects()
		self.removeAllToolTips()
		
		for i, annotation in enumerate(self.page.annotations()):
			if type(annotation) != PDFAnnotationLink:
				continue

			origin, size = annotation.bounds()
			rect = (self.transform.transformPoint_(origin),
			        self.transform.transformSize_(size))
			self.addCursorRect_cursor_(rect, NSCursor.pointingHandCursor())

			self.addToolTipRect_owner_userData_(rect, self, i)
	
	
	def view_stringForToolTip_point_userData_(self, view, tag, point, data):
		annotation = self.page.annotations()[data]
		return annotation.toolTip() or ""
	
	
	def keyDown_(self, event):
		if event.modifierFlags() & NSAlternateKeyMask:
			c = event.charactersIgnoringModifiers()
			if c == "i": # reset bbox to identity
				global bbox
				bbox = NSAffineTransform.transform()
		
		c = event.characters()
		
		if c == "q": # quit
			app.terminate_(self)
		
		elif c == chr(27): # esc
			toggle_fullscreen(fullscreen=False)
		
		elif c == "h":
			app.hide_(app)
		
		elif c == "?":
			self.show_help = not self.show_help
		
		elif c in "t ": # toogle clock/timer
			self.absolute_time = not self.absolute_time
			now = time.time()
			if self.absolute_time:
				self.elapsed_duration += (now - self.start_time)
			else:
				self.start_time = now

		elif c in "z[]{}": # timer management
			self.start_time = time.time()
			self.elapsed_duration = 0
			
			self.duration += {
				"{": -600,
				"[":  -60,
				"z":    0,
				"]":   60,
				"}":  600,
			}[c]
			self.duration = max(0, self.duration)
			self.duration_change_time = time.time()
		
		elif c in "+=-_0": # web view scale
			document = web_view.mainFrame().frameView().documentView()
			clip = document.superview()
			if c in "+=":
				scale = (1.1, 1.1)
			elif c in "-_":
				scale = (1./1.1, 1./1.1)
			else:
				scale = clip.convertSize_fromView_((1., 1.), None)
			clip.scaleUnitSquareToSize_(scale)
			document.setNeedsLayout_(True)
		
		else:
			action = {
				"f":                     toggle_fullscreen,
				"w":                     toggle_web_view,
				"m":                     toggle_movie_view,
				"s":                     presentation_show,
				NSUpArrowFunctionKey:    prev_page,
				NSLeftArrowFunctionKey:  prev_page,
				NSDownArrowFunctionKey:  next_page,
				NSRightArrowFunctionKey: next_page,
				NSHomeFunctionKey:       home_page,
				NSEndFunctionKey:        end_page,
				NSPageUpFunctionKey:     back,
				NSPageDownFunctionKey:   forward,
			}.get(c, nop)
			action()
		
		refresher.refresh_()

	def scrollWheel_(self, event):
		if not (event.modifierFlags() & NSAlternateKeyMask):
			return
		p = event.locationInWindow()
		p = self.transform.transformPoint_(p)
		bbox.translateXBy_yBy_(p.x, p.y)
		bbox.scaleBy_(exp(event.deltaY()*0.01))
		bbox.translateXBy_yBy_(-p.x, -p.y)
		refresher.refresh_()
	
	def mouseDown_(self, event):
		self.edit_bbox = event.modifierFlags() & NSAlternateKeyMask
	
	def mouseDragged_(self, event):
		if not self.edit_bbox:
			return
		delta = self.transform.transformSize_((event.deltaX(), -event.deltaY()))
		bbox.translateXBy_yBy_(delta.width, delta.height)
		refresher.refresh_()
	
	def mouseUp_(self, event):
		if self.edit_bbox:
			return
		
		point = self.transform.transformPoint_(event.locationInWindow())
		annotation = self.page.annotationAtPoint_(point)
		if annotation is None:
			return

		if type(annotation) != PDFAnnotationLink:
			return
		
		if annotation in movies:
			movie, _ = movies[annotation]
			movie_view.setMovie_(movie)
			presentation_show(movie_view)
			return
			
		action = annotation.mouseUpAction()
		destination = annotation.destination()
		url = annotation.URL()

		if type(action) == PDFActionNamed:
			action_name = action.name()
			action = {
				kPDFActionNamedNextPage:     next_page,
				kPDFActionNamedPreviousPage: prev_page,
				kPDFActionNamedFirstPage:    home_page,
				kPDFActionNamedLastPage:     end_page,
				kPDFActionNamedGoBack:       back,
				kPDFActionNamedGoForward:    forward,
#				kPDFActionNamedGoToPage:     nop,
#				kPDFActionNamedFind:         nop,
#				kPDFActionNamedPrint:        nop,
			}.get(action_name, nop)
			action()

		elif destination:
			goto_page(pdf.indexForPage_(destination.page()))
		
		elif url:
			web_view.mainFrame().loadRequest_(NSURLRequest.requestWithURL_(url))
		
		refresher.refresh_()


# window utils ###############################################################

def create_window(title, Window=NSWindow):
	window = Window.alloc().initWithContentRect_styleMask_backing_defer_screen_(
		PRESENTER_FRAME,
		NSMiniaturizableWindowMask|NSResizableWindowMask|NSTitledWindowMask,
		NSBackingStoreBuffered,
		NO,
		None,
	)
	window.setTitle_(title)
	window.makeKeyAndOrderFront_(nil)
	return window

def create_view(window, View=NSView):
	view = View.alloc().initWithFrame_(window.frame())
	window.setContentView_(view)
	window.setInitialFirstResponder_(view)
	return view

def add_subview(view, subview, autoresizing_mask=NSViewWidthSizable|NSViewHeightSizable):
	subview.setAutoresizingMask_(autoresizing_mask)
	subview.setFrameOrigin_((0, 0))
	view.addSubview_(subview)


# presentation window ########################################################

presentation_window = create_window(file_name)
presentation_view   = presentation_window.contentView()
frame = presentation_view.frame()

# slides

slide_view = SlideView.alloc().initWithFrame_(frame)
add_subview(presentation_view, slide_view)

# web view

web_view = WebView.alloc().initWithFrame_frameName_groupName_(frame, nil, nil)

class WebFrameLoadDelegate(NSObject):
	def webView_didCommitLoadForFrame_(self, view, frame):
		presentation_show(web_view)
web_frame_load_delegate = WebFrameLoadDelegate.alloc().init()
web_view.setFrameLoadDelegate_(web_frame_load_delegate)

add_subview(presentation_view, web_view)

# movie view

class MovieView(QTMovieView):
	def setHidden_(self, hidden):
		QTMovieView.setHidden_(self, hidden)
		if self.isHidden():
			self.pause_(self)
		else:
			self.play_(self)

movie_view = MovieView.alloc().initWithFrame_(frame)
movie_view.setPreservesAspectRatio_(True)

add_subview(presentation_view, movie_view)

# message view

if show_feed:
	frame.size.height = 40
	message_view = MessageView.alloc().initWithFrame_(frame)
	add_subview(presentation_view, message_view, NSViewWidthSizable)


# views visibility

def presentation_show(visible_view=slide_view):
	for view in [slide_view, web_view, movie_view]:
		view.setHidden_(view != visible_view)

def toggle_view(view):
	presentation_show(view if view.isHidden() else slide_view)

def toggle_web_view():   toggle_view(web_view)
def toggle_movie_view(): toggle_view(movie_view)

presentation_show()


# presenter window ###########################################################

presenter_window = create_window(file_name)
presenter_view   = create_view(presenter_window, PresenterView)

presenter_window.center()
presenter_window.makeFirstResponder_(presenter_view)


# handling full screens ######################################################

def toggle_fullscreen(fullscreen=None):
	_fullscreen = presenter_view.isInFullScreenMode()
	if fullscreen is None:
		fullscreen = not _fullscreen
	
	if fullscreen != _fullscreen:
		for window, screen in zip([presenter_window, presentation_window],
		                          NSScreen.screens()):
			view = window.contentView()
			if fullscreen:
				view.enterFullScreenMode_withOptions_(screen, {})
			else:
				view.exitFullScreenModeWithOptions_({})
		presenter_window.makeFirstResponder_(presenter_view)

	return _fullscreen


# application delegate #######################################################

def add_item(menu, title, action, key="", modifiers=NSCommandKeyMask, target=app):
	menu_item = menu.addItemWithTitle_action_keyEquivalent_(
		NSString.localizedStringWithFormat_(" ".join(("%@",) * len(title)), *(_s(s) for s in title)),
		action, key)
	menu_item.setKeyEquivalentModifierMask_(modifiers)
	menu_item.setTarget_(target)
	return menu_item
	
	
class ApplicationDelegate(NSObject):
	def about_(self, sender):
		app.orderFrontStandardAboutPanelWithOptions_({
			"ApplicationName":    _s(NAME),
			"Version":            _s(VERSION),
			"Copyright":          _s(COPYRIGHT),
			"ApplicationVersion": _s("%s %s" % (NAME, VERSION)),
			"Credits":            _h(CREDITS),
			"ApplicationIcon":    ICON,
		})
	
	def update_(self, sender):
		try:
			data, response, _ = NSURLConnection.sendSynchronousRequest_returningResponse_error_(
				NSURLRequest.requestWithURL_(NSURL.URLWithString_(HOME + "releases/version.txt")), None, None
			)
			assert response.statusCode() == 200 # found
		except:
			NSAlert.alertWithError_(
				NSError.errorWithDomain_code_userInfo_("unable to connect to internet,", 1, {})
			).runModal()
			return
		
		version = bytearray(data).decode("utf-8").strip()
		if version == VERSION:
			title   = "No update available"
			message = "Your version (%@) of %@ is up to date."
		else:
			title =   "Update available"
			message = "A new version (%@) of %@ is available."
		
		if NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
			title,
			"Go to website", "Cancel", None,
			message, version, _s(NAME),
		).runModal() != NSAlertDefaultReturn:
			return
		
		NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(HOME))
	
	
	def applicationDidFinishLaunching_(self, notification):
		main_menu = NSMenu.alloc().initWithTitle_("MainMenu")
		
		application_menuitem = main_menu.addItemWithTitle_action_keyEquivalent_("Application", None, " ")
		application_menu = NSMenu.alloc().initWithTitle_("Application")
#		app.setAppleMenu_(application_menu)
		
		add_item(application_menu, ["About", NAME], "about:", target=self)
		add_item(application_menu, ["Check for updates…"], "update:", target=self)
		application_menu.addItem_(NSMenuItem.separatorItem())
		add_item(application_menu, ["Hide", NAME], "hide:", "h")
		add_item(application_menu, ["Hide Others"], "hideOtherApplications:", "h", NSCommandKeyMask | NSAlternateKeyMask)
		add_item(application_menu, ["Show All"], "unhideAllApplications:")
		application_menu.addItem_(NSMenuItem.separatorItem())
		add_item(application_menu, ["Quit", NAME], "terminate:", "q")
		main_menu.setSubmenu_forItem_(application_menu, application_menuitem)
		
		app.setMainMenu_(main_menu)
		
		app.setApplicationIconImage_(ICON)
	
	
	def applicationWillHide_(self, notification):
		self.fullscreen = toggle_fullscreen(fullscreen=False)
	
	def applicationDidUnhide_(self, notification):
		toggle_fullscreen(fullscreen=self.fullscreen)
	
	def applicationWillTerminate_(self, notification):
		presentation_show()

application_delegate = ApplicationDelegate.alloc().init()
app.setDelegate_(application_delegate)


# HACK: ensure ApplicationDelegate.applicationDidFinishLaunching_ is called
if launched_from_finder:
	NSNotificationCenter.defaultCenter().postNotificationName_object_(
		NSApplicationDidFinishLaunchingNotification, app)


# main loop ##################################################################

class Refresher(NSObject):
	def refresh_(self, timer=None):
		for window in app.windows():
			window.contentView().setNeedsDisplay_(True)
refresher = Refresher.alloc().init()

refresher_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
	1.,
	refresher, "refresh:",
	nil, YES)

sys.exit(app.run())
