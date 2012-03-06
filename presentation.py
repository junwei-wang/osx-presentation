#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

# imports ####################################################################

import sys
import os
import time

from objc import *
from Foundation import *
from Cocoa import *
from Quartz import *


# constants ##################################################################

PRESENTER_FRAME = ((100., 100.), (640., 480.))


# handling args ##############################################################

name, args = sys.argv[0], sys.argv[1:]
assert len(args) == 1, "usage"

path = args[0]


# application init ###########################################################

pool = NSAutoreleasePool.alloc().init()
app = NSApplication.sharedApplication()


# opening presentation #######################################################

url = NSURL.fileURLWithPath_(path)
pdf = PDFDocument.alloc().initWithURL_(url)

#page = pdf.pageAtIndex_(0)
#for an in  page.annotations():
#	action = an.mouseUpAction()
#	print an.bounds()
#	t = type(action)
#	if t == PDFActionGoTo:
#		print action.destination()
#	elif t == PDFActionURL:
#		print action.URL()
#	elif t == PDFActionNamed:
#		print action.name()

#	kPDFActionNamedNone = 0, 
#    kPDFActionNamedNextPage = 1, 
#    kPDFActionNamedPreviousPage = 2, 
#    kPDFActionNamedFirstPage = 3, 
#    kPDFActionNamedLastPage = 4, 
#    kPDFActionNamedGoBack = 5, 
#    kPDFActionNamedGoForward = 6, 
#    kPDFActionNamedGoToPage = 7, 
#    kPDFActionNamedFind = 8, 
#    kPDFActionNamedPrint = 9, 
#    kPDFActionNamedZoomIn = 10, 
#    kPDFActionNamedZoomOut = 11


page_count = pdf.pageCount()
current_page = 0

class Redisplayer(NSObject):
	def display_(self, timer=None):
		for window in app.windows():
			window.display()
redisplayer = Redisplayer.alloc().init()

def goto_page(page):
	global current_page
	current_page = min(max(0, page), page_count-1)
	redisplayer.display_()


# handling full screens ######################################################

fullscreen = False
def toggle_fullscreen():
	global fullscreen
	for window, screen in reversed(zip(app.windows(), NSScreen.screens())):
		view = window.contentView()
		if fullscreen:
			view.exitFullScreenModeWithOptions_({})
		else:
			view.enterFullScreenMode_withOptions_(screen, {}) 
		window.makeFirstResponder_(view)
	fullscreen = not fullscreen


# presenter view #############################################################

class PresenterView(NSView):
	def drawRect_(self, rect):
		bounds = self.bounds()
		width, height = bounds.size

		margin = width / 20
		current_width = width / 2
		font_size = margin / 3
	
		NSRectFillUsingOperation(bounds, NSCompositeClear)

		# current 
		page = pdf.pageAtIndex_(current_page)
		_, (w, h) = page.boundsForBox_(kPDFDisplayBoxCropBox)
		r = current_width/w
	
		transform = NSAffineTransform.transform()
		transform.translateXBy_yBy_(margin, height/2.)
		transform.scaleXBy_yBy_(r, r)
		transform.translateXBy_yBy_(0., -h/2.)
		transform.concat()

		page.drawWithBox_(kPDFDisplayBoxCropBox)
		transform.invert()
		transform.concat()
	
		# page number
		page_number = NSString.stringWithString_("%s/%s" % (current_page+1, page_count))
		page_number.drawAtPoint_withAttributes_((margin, (height+h*r+font_size)/2.), {
			NSFontAttributeName:            NSFont.labelFontOfSize_(font_size),
			NSForegroundColorAttributeName: NSColor.whiteColor(),
		})

		# time
		now = NSString.stringWithString_(time.strftime("%H:%M:%S"))
		now.drawAtPoint_withAttributes_((margin, margin), {
			NSFontAttributeName:            NSFont.labelFontOfSize_(margin),
			NSForegroundColorAttributeName: NSColor.whiteColor(),
		})
	
		# next page
		try:
			page = pdf.pageAtIndex_(current_page+1)
		except:
			return
		_, (w, h) = page.boundsForBox_(kPDFDisplayBoxCropBox)
		r = (width - (3*margin + current_width))/w
	
		transform = NSAffineTransform.transform()
		transform.translateXBy_yBy_(2*margin+current_width, height/2.)
		transform.scaleXBy_yBy_(r, r)
		transform.translateXBy_yBy_(0., -h/2.)
		transform.concat()

		page.drawWithBox_(kPDFDisplayBoxCropBox)
		transform.invert()
		transform.concat()
	
	
	def keyDown_(self, event):
		c = event.characters()
		if c == "f":
			toggle_fullscreen()
		
		elif c in [u"\uf700", u"\uf702"]:
			goto_page(current_page-1)
		
		elif c in [u"\uf701", u"\uf703"]:
			goto_page(current_page+1)
		
		elif c == "q":
			app.terminate_(self)


# presentation ###############################################################

class PresentationView(NSView):
	def drawRect_(self, rect):
		bounds = self.bounds()
		width, height = bounds.size
		
		NSRectFillUsingOperation(bounds, NSCompositeClear)
	
		# current page
		page = pdf.pageAtIndex_(current_page)
		_, (w, h) = page.boundsForBox_(kPDFDisplayBoxCropBox)
		r = min(width/w, height/h)
	
		transform = NSAffineTransform.transform()
		transform.translateXBy_yBy_(width/2., height/2.)
		transform.scaleXBy_yBy_(r, r)
		transform.translateXBy_yBy_(-w/2., -h/2.)
		transform.concat()

		page.drawWithBox_(kPDFDisplayBoxCropBox)
		transform.invert()
		transform.concat()


# windows ####################################################################

# presenter window
presenter_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_screen_(
	PRESENTER_FRAME,
	NSMiniaturizableWindowMask|NSResizableWindowMask|NSTitledWindowMask,
	NSBackingStoreBuffered,
	NO,
	None,
)
presenter_window.setTitle_(name)
	
presenter_view = PresenterView.alloc().initWithFrame_(presenter_window.frame())
presenter_window.setContentView_(presenter_view)
presenter_window.setInitialFirstResponder_(presenter_view)
presenter_window.makeFirstResponder_(presenter_view)
	
# presentation window
presentation_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_screen_(
	PRESENTER_FRAME,
	NSMiniaturizableWindowMask|NSResizableWindowMask|NSTitledWindowMask,
	NSBackingStoreBuffered,
	NO,
	None,
)
presentation_window.setTitle_(name)

presentation_view = PresentationView.alloc().initWithFrame_(presentation_window.frame())
presentation_window.setContentView_(presentation_view)
presentation_window.setInitialFirstResponder_(presentation_view)

presenter_window.makeKeyAndOrderFront_(nil)
	
# redisplay
redisplay_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
	1.,
	redisplayer, "display:",
	nil, YES)
		
# main loop ##################################################################

sys.exit(app.run())
