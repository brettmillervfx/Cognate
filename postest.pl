
can_traverse(X,Y) :- path(X,Y), open(X,Y)
open(X,Y) :- boundary(D,X,Y), open(D)

path(under_the_window,outside)
boundary(window,under_the_window,outside)
open(window)



