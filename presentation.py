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
	Usage: %s [-hvd:f] <doc.pdf>
		-h --help          print this help message then exit
		-v --version       print version then exit
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


# options

try:
	options, args = getopt.getopt(args, "hvd:f", ["help", "version", "duration=", "feed"])
except getopt.GetoptError as message:
	exit_usage(message, 1)

show_feed = False
presentation_duration = 0

for opt, value in options:
	if opt in ["-h", "--help"]:
		exit_usage()
	elif opt in ["-v", "--version"]:
		exit_version()
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
	NSObject, NSTimer, NSError, NSString,
	NSAttributedString, NSUnicodeStringEncoding,
	NSURL, NSURLRequest, NSURLConnection,
	NSAffineTransform, NSMakeSize,
)

from AppKit import (
	NSApplication,
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
	NSScreen, NSWorkspace,
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
		delta = NSMakeSize(event.deltaX(), -event.deltaY())
		delta = self.transform.transformSize_(delta)
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
	
	def applicationWillHide_(self, notification):
		self.fullscreen = toggle_fullscreen(fullscreen=False)
	
	def applicationDidUnhide_(self, notification):
		toggle_fullscreen(fullscreen=self.fullscreen)
	
	def applicationWillTerminate_(self, notification):
		presentation_show()

application_delegate = ApplicationDelegate.alloc().init()
app.setDelegate_(application_delegate)


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
