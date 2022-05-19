% not(container(barf))
% container(box)
% container(barrel)
% container(chest)

% contains(box, nothing)
% contains(barrel, nothing)
% contains(chest, banana)

% openable(box)
% openable(chest)

% container rules
% empty(X) :- contains(X, nothing)

% negation works
open(box)
brown(brick)
blue(sack)
closed(X) :- not(open(X))

% what about 'and'
poop(X) :- brown(X),closed(X)

% what about 'or' -- no but you don't actually need it.
bag(X) :- blue(X)
bag(X) :- open(X)

% at some point I need to make sure we fail on this type of thing:
% zork(ZZ)! 2342