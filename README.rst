===============
presentation.py
===============

a pdf presentation tool for Mac OS X


Features
--------

A multi-screen presentation tool for pdf on the mac, with some (more or less) useful features:


- a presenter view that shows the current and next slides, the current time or a (countdown) timer, the notes attached to the pdf;
- interactive links in the current slide preview (internal links go to the corresponding page, URLs are opened in the presenter view);
- presentation view that display the current slide fullscreen and can be toggled to a full screen web view; and
- a scrolling banner that reads its text from stdin.


Usage
-----

::

	Usage: ./presentation.py [-hd:f] <doc.pdf>
		-h --help          this help message
		-d --duration <t>  duration of the talk in minutes
		-f --feed          enable reading feed on stdin
		<doc.pdf>          pdf to present


Key bindings
------------

::

	'h'          show this help
	'q'          quit
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
