## Signpost — what a checkpoint is for

*Licence: CC BY-SA 4.0 (D-101, 2026-10-01; the story strand was all rights reserved under D-64 until then).*

Where we are: the first real model trained for seven hours and the machine froze. The run
survived on a checkpoint written ten minutes earlier, and the chapter you have just read is
mostly about the two ways it could have been lost anyway — a script that deletes the old
checkpoint on restart, a save that overwrites in place. Both are fixed; both are the kind of
thing nobody writes down until it costs them a night.

The same discipline is what made the next two chapters possible. When a rented machine is
running at forty-nine cents an hour, "copy the checkpoint at the moment the phase switches"
is a one-line watcher, and that one line is why the shelf could be tested at all: two models
had to start from an identical point, and the watcher had kept it. It is also why the run that
destroyed itself in Chapter 10 cost fifty cents to redo rather than seven dollars. Save early,
save atomically, keep the one you would want if the lights went out now.

Next: the app on the stick.
