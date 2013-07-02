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

from math import exp
from collections import defaultdict


# constants and helpers ######################################################

NAME = "Présentation"
MAJOR, MINOR = 0, 6
VERSION = "%s.%s" % (MAJOR, MINOR)
COPYRIGHT = "Copyright © 2011-2013 Renaud Blanch"

PRESENTER_FRAME = ((100., 100.), (1024., 768.))

def nop(): pass

def print_help():
	sys.stderr.write(textwrap.dedent("""\
		'h'          show this help
		'q', esc     quit
		'w'          toggle web view
		'f'          toggle fullscreen
		up, left     previous page
		down, right  next page
		home         first page
		end          last page
		page up      back
		page down    forward
		't'          switch between clock and timer
		'z'          set origin for timer
		']'          add 1 minute to planned time
		'['          sub 1 minute
		'}'          add 10 minutes
		'{'          sub 10 minutes
	"""))


# handling args ##############################################################

name, args = sys.argv[0], sys.argv[1:]

if args and args[0].startswith("-psn"):
	# we have been launched by the finder, ignore this command line switch
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

from objc import *
from Foundation import *
from Cocoa import *
from Quartz import *
from WebKit import *

objc.setVerbose(1)

if sys.version_info[0] == 3:
	_ = lambda s: s
else:
	_ = NSString.alloc().initWithUTF8String_


app = NSApplication.sharedApplication()
app.activateIgnoringOtherApps_(True)

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
	toggle_web_view(visible=False)

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


# notes

notes = defaultdict(list)
for page_number in range(page_count):
	page = pdf.pageAtIndex_(page_number)
	page.setDisplaysAnnotations_(False)
	for annotation in page.annotations():
		if type(annotation) == PDFAnnotationText:
			notes[page_number].append(annotation.contents())

# bbox

bbox = NSAffineTransform.transform()


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
		bbox.concat()

		NSEraseRect(page_rect)
		page.drawWithBox_(kPDFDisplayBoxCropBox)
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
	duration = presentation_duration * 60. + 1.
	absolute_time = False
	start_time = time.time()
	
	def drawRect_(self, rect):
		bounds = self.bounds()
		width, height = bounds.size

		margin = width / 20
		current_width = width / 2
		font_size = margin / 3
	
		NSRectFillUsingOperation(bounds, NSCompositeClear)

		# current 
		self.page = pdf.pageAtIndex_(current_page)
		page_rect = self.page.boundsForBox_(kPDFDisplayBoxCropBox)
		_, (w, h) = page_rect
		r = current_width/w
		
		NSGraphicsContext.saveGraphicsState()
		transform = NSAffineTransform.transform()
		transform.translateXBy_yBy_(margin, height/2.)
		transform.scaleXBy_yBy_(r, r)
		transform.translateXBy_yBy_(0., -h/2.)
		transform.concat()
		
		NSGraphicsContext.saveGraphicsState()
		
		bbox.concat()
		NSEraseRect(page_rect)
		self.page.drawWithBox_(kPDFDisplayBoxCropBox)
		
		# links
		NSColor.blueColor().setFill()
		for annotation in self.page.annotations():
			annotation_type = type(annotation)
			if annotation_type == PDFAnnotationLink:
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
		if self.absolute_time:
			clock = time.localtime()
		else:
			clock = time.gmtime(abs(self.duration - (time.time() - self.start_time)))
		clock = NSString.stringWithString_(time.strftime("%H:%M:%S", clock))
		clock.drawAtPoint_withAttributes_((margin, height-margin*2), {
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
		                                         height-margin*2.), attr)

		# notes
		note = NSString.stringWithString_("\n".join(notes[current_page]))
		note.drawAtPoint_withAttributes_((margin, margin), {
			NSFontAttributeName:            NSFont.labelFontOfSize_(font_size),
			NSForegroundColorAttributeName: NSColor.whiteColor(),
		})
		
		# next page
		try:
			page = pdf.pageAtIndex_(current_page+1)
		except:
			return
		page_rect = page.boundsForBox_(kPDFDisplayBoxCropBox)
		_, (w, h) = page_rect
		r = (width - (3*margin + current_width))/w
	
		NSGraphicsContext.saveGraphicsState()
		transform = NSAffineTransform.transform()
		transform.translateXBy_yBy_(2*margin+current_width, height/2.)
		transform.scaleXBy_yBy_(r, r)
		transform.translateXBy_yBy_(0., -h/2.)
		transform.concat()
		bbox.concat()

		NSEraseRect(page_rect)
		page.drawWithBox_(kPDFDisplayBoxCropBox)
		NSGraphicsContext.restoreGraphicsState()
		
	
	def resetCursorRects(self):
		self.discardCursorRects()
		for annotation in self.page.annotations():
			annotation_type = type(annotation)
			if annotation_type == PDFAnnotationLink:
				origin, size = annotation.bounds()
				rect = (self.transform.transformPoint_(origin),
				        self.transform.transformSize_(size))
				self.addCursorRect_cursor_(rect, NSCursor.pointingHandCursor())
	
	
	def keyDown_(self, event):
		if (event.modifierFlags() & NSAlternateKeyMask):
			c = event.charactersIgnoringModifiers()
			if c == "i": # reset bbox to identity
				global bbox
				bbox = NSAffineTransform.transform()
		
		c = event.characters()

		if c in ["q", chr(27)]: # quit
			app.terminate_(self)
		
		elif c == "t": # switch time representation
			self.absolute_time = not self.absolute_time

		elif c == "z": # reset timer
			self.start_time = time.time()
		
		elif c == "[":
			self.duration -= 60.
		
		elif c == "]":
			self.duration += 60.

		elif c == "{":
			self.duration -= 600.
		
		elif c == "}":
			self.duration += 600.
		
		else:
			action = {
				"h":                     print_help,
				"f":                     toggle_fullscreen,
				"w":                     toggle_web_view,
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

presentation_window = create_window(name)
presentation_view   = presentation_window.contentView()
frame = presentation_view.frame()

# slides

slide_view = SlideView.alloc().initWithFrame_(frame)
add_subview(presentation_view, slide_view)

# web view

web_view = WebView.alloc().initWithFrame_frameName_groupName_(frame, nil, nil)
def toggle_web_view(visible=None):
	if visible is None:
		visible = web_view.isHidden()
	slide_view.setHidden_(visible)
	web_view.setHidden_(not visible)
toggle_web_view(False)

class WebFrameLoadDelegate(NSObject):
	def webView_didFinishLoadForFrame_(self, view, frame):
		toggle_web_view(visible=True)
web_frame_load_delegate = WebFrameLoadDelegate.alloc().init()
web_view.setFrameLoadDelegate_(web_frame_load_delegate)

add_subview(presentation_view, web_view)

# message view

if show_feed:
	frame.size.height = 40
	message_view = MessageView.alloc().initWithFrame_(frame)
	add_subview(presentation_view, message_view, NSViewWidthSizable)


# presenter window ###########################################################

presenter_window = create_window(name)
presenter_view   = create_view(presenter_window, PresenterView)

presenter_window.center()
presenter_window.makeFirstResponder_(presenter_view)


# handling full screens ######################################################

def toggle_fullscreen():
	for window, screen in reversed(zip(reversed(app.windows()),
	                                   NSScreen.screens())):
		view = window.contentView()
		if view.isInFullScreenMode():
			view.exitFullScreenModeWithOptions_({})
		else:
			view.enterFullScreenMode_withOptions_(screen, {})
		window.makeFirstResponder_(view)



# application delegate #######################################################

def add_item(menu, title, action, key="", modifiers=NSCommandKeyMask, target=app):
	menu_item = menu.addItemWithTitle_action_keyEquivalent_(
		NSString.localizedStringWithFormat_(" ".join(("%@",) * len(title)), *(_(s) for s in title)),
		action, key)
	menu_item.setKeyEquivalentModifierMask_(modifiers)
	menu_item.setTarget_(target)
	return menu_item
	
	
class ApplicationDelegate(NSObject):
	def about_(self, sender):
		app.orderFrontStandardAboutPanelWithOptions_({
			"ApplicationName":    _(NAME),
			"Version":            _(VERSION),
			"Copyright":          _(COPYRIGHT),
			"ApplicationVersion": _("%s %s" % (NAME, VERSION)),
		})
	
	def update_(self, sender):
		HOME = "http://iihm.imag.fr/blanch/software/osx-presentation/"
		try:
			data, response, _sentinel = NSURLConnection.sendSynchronousRequest_returningResponse_error_(
				NSURLRequest.requestWithURL_(NSURL.URLWithString_(HOME + "releases/version.txt")), None, None
			)
			assert response.statusCode() == 200 # found
		except:
			NSAlert.alertWithError_(
				NSError.errorWithDomain_code_userInfo_("unable to connect to internet,", 1, {})
			).runModal()
			return
		
		version = data.bytes().tobytes().decode("utf-8")
		if version == VERSION:
			return
		
		if NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
			"Update available",
			"Go to website", "Cancel", None,
			"A new version (%@) of %@ is available.",
			version,
			_(NAME),
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
