

blocked(X,Y) :- interface(D,X,Y), closed(D)

can_traverse(X,Y) :- path(X,Y), not(blocked(X,Y))
can_traverse(Y,X) :- path(X,Y), not(blocked(X,Y))

closed(X) :- door(X), not(open(X))

at(X,L) :- interface(X,L,_)
at(X,L) :- interface(X,_,L)

foo(A,B) :- bar(A,_,E), baz(_,B,E)
bar(apple,banana,egg)
baz(cherry,durian,egg)

door(window)
open(window)
interface(window,under_the_window,outside)
path(under_the_window,outside)

door(front_door)
interface(front_door,foyer,outside)
path(foyer_outside)

