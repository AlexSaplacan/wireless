Wireless is a blender addon

It lets you easily tranform a curve into a cable of predefined shape and 
gives the option to add a tail and / or a head at the extremities.

This way you can quickly create an usb cable, or a rope with knots , or a lead with 
electric sockets.

At the moment you are able to turn on and off wireless on a curve, it loads a default cable type.

Next steps to implement:

1.a Be able to change the cable from the thumbnails collection.
	- cable_preview_update function (wireless_props.py)

1.b Make thumbnail collection load only cables thumbs, not heads/tails

1.c  Be able to change the cable type from previous / next buttons 
	-OBJECT_OT_Cable_Previous operator
	-OBJECT_OT_Cable_Next operator

2 HEAD and TAIL
these are quite similar so do one and copy the other , will need to add different props for each.
Similar UI as the cable part, will stay hidden until enabled with the radio button ()

3 Enchantments 

3.1 Be able to scale the radius of the cable
3.2 Be able to choose different categories of cables / heads like:
	-electrical
	-data
	-ropes
	-chains?? - maybe will require extra scripting
	-and others



