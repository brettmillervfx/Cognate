%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Escape Room
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% path rules
open(X,Y) :- interface(D,X,Y), open(D)

can_traverse(X,Y) :- path(X,Y), open(X,Y)
can_traverse(Y,X) :- path(X,Y), open(X,Y)

% door rules
% Agent, Door, Location
can_open(A,D) :- door(D), unlocked(D), closed(D), next_to(A,D)


can_close(A,D) :- door(D), open(D), next_to(A,D)
can_lock(A,D) :- lockable_door(D), unlocked(D), next_to(A,D), closed(D)
can_unlock(A,D) :- lockable_door(D), locked(D), next_to(A,D), closed(D)

lockable_door(D) :- door(D), lockable(D)
%closed(D) :- locked(D)
closed(D) :- not(open(D))

at(X,L) :- interface(X,L,_)
at(X,L) :- interface(X,_,L)
next_to(A,I) :- at(I,L), at(A,L)

% instances
path(under_the_window,by_the_door)
open(under_the_window,by_the_door)
path(by_the_bed,by_the_door)
open(by_the_bed,by_the_door)
path(by_the_door,under_the_window)
open(by_the_door,under_the_window)
path(under_the_window,by_the_closet)
open(under_the_window,by_the_closet)
path(by_the_closet,in_the_closet)
path(under_the_window,outside)
path(by_the_door,outside)

door(closet_door)
interface(closet_door,by_the_closet,in_the_closet)
unlocked(closet_door)
%open(closet_door)

door(front_door)
lockable(front_door)
locked(front_door)
interface(front_door,by_the_door,outside)

door(window)
lockable(window)
locked(window)
closed(window)
interface(window,under_the_window,outside)

item(key)
at(key,in_the_closet)

person(agent)

% initial state
% has(agent,key)
%at(agent,by_the_door)
at(agent,by_the_closet)
%at(agent,under_the_window)



