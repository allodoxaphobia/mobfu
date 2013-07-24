mobfu
=====
Attack tool/fuzzer for SMS services.
Currently still very much in the conceptual state this tool will be capable, by means of a serial modem to send
SMS' with fuzzed payloads to a recipient.

Future Capabilities:
===================
	- data field fuzzing
	- data header field fuzzing
	- test wether receiver overwrites messages (duplicate handling)
	- test validity enforcement
	- test different encodings
	- test handling of multipart messages

Every SMS can/will be be tagged with a unique identifier to facilitiate log inspection on the device/Servic eunder test.

Current Capabilities
======================
- send SMS to recipient
- load list of values and send them: usefull for fuzzing or bruteforce attacks

Usage
=====
run "./mobfu.py -h" for help


