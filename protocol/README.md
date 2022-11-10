# Messaging and RUDP

This folder contains the code that implements the Messeging and
RUDP protocol allowing clients to communicate with the server.

## RUDP (Reliable User Datagram Protocol)

`RUDP` is our implementation of a protocol that for the reliable sending of messages
between a client and server. It does this by adding two things on top of UDP:

1. Guaranteed arrival. through timing, resending, and acknowledgement signals,
   the message is guaranteed to reach the destination.
2. Correct data. The data received by the receiver is guaranteed to be the
   same data sent by the sender.

## Messaging Protocol

The messgaing protocol is specific to the application. It sits on top of RUDP and works
in a similar way to HTTP, in that a message has a method and a body.

A message is a string, where the first line is the method. Arguments/data are added as subsequent
lines:

```http
METHOD
ARG_1
ARG_2
...
ARG_n
```

### Request message

The request message contains a header line with a body line if applicable. The header line specifies
an action that the client would like the server to perform. The body line provides additional
information if required. The format is shown below:

```
Method: action
Data: '{"key":"value"}'
```

Possible values for the method are: FETCH, MESSAGE, LOGIN, EXIT. FETCH is used
fetch messages since the provided timestamp. MESSAGE lets the client send a
message provided. LOGIN authorizes a client to be able to send/receive messages.
EXIT lets the server know the client has terminated.

The data is a serialized version of a python dictionary. This is done using the
json library using the dumps (convert a python dictionary to a string) and loads
(convert a string into a python dictionary). Example request formats for each
method is provided below.

#### LOGIN format

```
Method: LOGIN
Data:'{"username": "john"}'
```

#### FETCH format

```
Method: FETCH
Data:'{"timestamp": 1646486140.689381}'
```

#### MESSAGE format

```
Method: MESSAGE
Data:'{"message": "Hello there!"}'
```

#### EXIT format

```
Method: EXIT
```

### Response message

Response messages from the sever contains two header lines with a body line. The
header lines state the status name followed by the status message. The body line
contains data if requested by client. The format is as follows:

```
Status-name: name
Status-message: message
Data: serializedData
```

Possible values for the status name are: AUTHORIZATION-ERROR, DATA-REQUIRED,
UNSUPPORTED-METHOD, FORMAT-ERROR, SUCCESS. AUTHORIZATION-ERROR specifies an error
with either carrying out the LOGIN request or when performing other requests without
having been authorized. DATA-REQUIRED is when the request body line doesn't exist
or value required is not within this body line. UNSUPPORTED-METHOD when the request
method provided is not handled for. FORMAT-ERROR when the request message is not
in a form recognizable to the server. SUCCESS when a request was completed with no
errors.

The status message header line provides more information regarding the status name
of the response.

The data body line will contain serialized data corresponding to the request method
and is parsable using json loads method. Two examples responses are provided below.

```
Status-name: AUTHORIZATION-ERROR
Status-message: Username is already taken
```

```
Status-name: SUCCESS
Status-message: Messages successfully fetched
Data: '[{"username":"John", "message":"Hi everyone", "timestamp":1646486140.689381}]'
```

### Methods

> NB: The reply value is the string the server sends back to the client after executing a method.

#### 1. LOGIN

Arguments:

1. Username

Reply value:

- Empty string

Eample:

```http
LOGIN
spongebob
```

#### 2. SEND_TEXT

Arguments:

1. Room id. Since we have only one room, it should always be `default`.
2. The encoded text to send. Encoding the text here means replacing newlines
   with a character/characters so that the text is one line in the protocol.
   The decoder will decode will insert back the newlines.

Reply value:

- Empty string

Eample:

```http
SEND_TEXT
default
hello beautiful people!
```

#### 3. GET_TEXTS

Arguments:

1. Unix Time stamp in milliseconds. Only messages sent after this time will be returned.

Reply value:

- Empty string

Eample:

```http
GET_TEXTS
1646136997205
```
