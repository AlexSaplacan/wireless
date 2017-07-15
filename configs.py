def init():

	#########################################
	#  logging stuff
	# import logging
	
	
	
	# ch = logging.StreamHandler()
	# # set debug level here
	# # ########################
	# ch.setLevel(logging.DEBUG)
	# # ########################
	# # global formatter
	# formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
	# ch.setFormatter(formatter)

	# log = logging.getLogger('wrls.configs')
	# log.setLevel(logging.DEBUG)

	##########################################
	# data handling

	import os
	import json

	json_path = os.path.join(os.path.dirname(__file__),"configs.json")

	global data
	with open(json_path) as data_file:
		data = json.load(data_file)

	# #########################################

	global thumbs
	thumbs = {}

	# to avoid loops
	global switch
	switch = False
