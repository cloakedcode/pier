# Parser

Parses code and spits out block comments, nicely broken down.

### See
[parseComments](#parseComments)

<a name='parseFile'><h2>parseFile</a></h2>

    parseFile(self, file)

Parse comments in the given file.

### Parameters
<table>
 <tr><td>file</td><td>String</td><td>Path of file.</td></tr>
</table>

### Returns
Array 

### See
[parseComments](#parseComments)

[MarkdownTemplate::renderComments](Parser#renderComments)

<a name='parseComments'><h2>parseComments</a></h2>

    parseComments(self, str)

Parse comments in the given code.

### Parameters
<table>
 <tr><td>str</td><td>String</td><td>String to parse.</td></tr>
</table>

### Returns
Array 

### See
[parseComment](#parseComment)

<a name='parseComment'><h2>parseComment</a></h2>

    parseComment(self, s)

Parse the given comment `s`.

The comment object returned contains the following

 - `tags`  array of tag objects
 - `description` the first line of the comment
 - `body` lines following the description
 - `content` both the description and the body
 - `isPrivate` True when "@api private" is used

### Parameters
<table>
 <tr><td>s</td><td>String</td><td></td></tr>
</table>

### Returns
Dictionary 

### See
[parseTag](#parseTag)

<a name='parseTag'><h2>parseTag</a></h2>

    parseTag(self, str)

Parse tag string "@param {Array} name description" etc.

### Parameters
<table>
 <tr><td>str</td><td>String</td><td></td></tr>
</table>

### Returns
Dictionary 

<a name='parseTagTypes'><h2>parseTagTypes</a></h2>

    parseTagTypes(self, str)

Parse tag type string "{Array|Object}" etc.

### Parameters
<table>
 <tr><td>str</td><td>String</td><td></td></tr>
</table>

### Returns
Array 

<a name='parseCodeContext'><h2>parseCodeContext</a></h2>

    parseCodeContext(self, str)

Parse the context from the given `str` of code.

This method attempts to discover the context
for the comment based on it's code.

### Parameters
<table>
 <tr><td>str</td><td>String</td><td></td></tr>
</table>

### Returns
Dictionary 

# MarkdownTemplate

Turns comments into markdown.

<a name='renderComments'><h2>renderComments</a></h2>

    renderComments(self, comments)

Renders a bunch of comments as markdown.

