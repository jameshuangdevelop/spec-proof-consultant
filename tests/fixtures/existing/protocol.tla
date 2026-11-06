---- MODULE protocol ----
VARIABLES state
Init == state = 0
Next == state' = 1 - state
====
