#! /usr/bin/python

import re

class Parser:
    langs = {
        'py' : {
            'class' : r'class (?P<name>[^\(]+)',
            'function' : r'def (?P<name>.+):',
            'comment_begin' : '"""',
            'comment_middle' : '',
            'comment_end' : '"""',
        },
        'php' : {
            'class' : r'class (?P<name>[^\(]+)',
            'function' : r'function (?P<name>.+):',
            'comment_begin' : '/*',
            'comment_middle' : '*',
            'comment_end' : '*/',
        },
    }

    """
      Parse comments in the given string of `js`.
     
      @param {String} js
      @return {Array}
      @see exports.parseComment
      @api public
    """
    def parseComments(self, str, ftype):
        self.lang = self.langs[ftype]

        comments = []
        comment = {}
        buf = ''
        ignore = False
        within = False
        code = ''

        comment_begin = self.lang['comment_begin']
        comment_end = self.lang['comment_end']
        len_begin = len(comment_begin)
        len_end = len(comment_end)

        i = 0
        while i < len(str):
            # start comment
            if within == False and str[i:i+len_begin] == comment_begin and (str[i-1] in ['', ' ', '\n', '\t']):
                # code following previous comment
                if buf.strip() and len(comments) > 0:
                    comment = comments[len(comments) - 1]
                    comment['code'] = code = buf.strip()
                    comment['ctx'] = self.parseCodeContext(code)
                buf = ''
                i += len_begin
                within = True
                ignore = ('!' == str[i + len_begin + 1])
            # end comment
            elif within and str[i:i+len_end] == comment_end and (str[i-1] in ['', ' ', '\n', '\t']):
                i += len_end
                buf = re.sub(re.escape(self.lang['comment_middle']), '', buf)
                comment = self.parseComment(buf)
                comment['ignore'] = ignore
                comments.append(comment)

                within = False
                ignore = False
                buf = ''
            # buffer comment or code
            else:
                buf += str[i]
                i += 1
        
        # trailing code
        if len(buf.strip()):
            comment = comments[len(comments) - 1]
            code = buf.strip()
            comment['code'] = code
            comment['ctx'] = self.parseCodeContext(code)

        return comments
    
    """
     Parse the given comment `str`.
     
     The comment object returned contains the following
     
      - `tags`  array of tag objects
      - `description` the first line of the comment
      - `body` lines following the description
      - `content` both the description and the body
      - `isPrivate` True when "@api private" is used
     
     @param {String} str
     @return {Object}
     @see exports.parseTag
     @api public
    """

    def parseComment(self, s):
        s = s.strip()
        comment = {'tags' : []}
        description = {}
        
        # remove the same number of spaces/tabs before each line of the comment (counteracts indenting)
        spaces = re.match('\s*', s.splitlines()[1]).group(0)
        s = re.sub(spaces, '', s, re.MULTILINE)

        # split the description and tags
        pieces = re.split('\s+@', s)

        description['full'] = pieces[0] or s
        # split summary and body (two line breaks, both possibly followed by spaces/tabs
        desc = re.split('\n', description['full'])
        description['summary'] = desc[0]
        description['body'] = ''
        if len(desc) > 1:
            body = '\n'.join(desc[1:])
            
            description['body'] = body

        comment['description'] = description
        
        # parse tags
        if len(pieces) > 1:
            comment['tags'] = map(self.parseTag, pieces[1:])
            for t in comment['tags']:
                if t['type'] == 'api' and t['visibility'] == 'private':
                    comment['isPrivate'] = True
                    break
        
        return comment
    
    """
     Parse tag string "@param {Array} name description" etc.
     
     @param {String}
     @return {Object}
     @api public
    """

    def parseTag(self, str):
        parts = str.strip().split(' ')
        tag = {} 
        tag['type'] = parts.pop(0)
        type = tag['type']

        if type == 'param':
            tag['types'] = self.parseTagTypes(parts[0])
            tag['name'] = parts[1:] or ''
            tag['description'] = ' '.join(parts[2:] or '')
        elif type == 'return':
            tag['types'] = self.parseTagTypes(parts[0])
            tag['description'] = ' '.join(parts[1:])
        elif type == 'see':
            if str.find('http'):
                tag['title'] = parts.pop(0) or ''
                tag['url'] = ' '.join(parts)
            else:
                tag['local'] = ' '.join(parts)
        elif type == 'api':
            tag['visibility'] = parts[0]
        elif type == 'type':
            tag['types'] = self.parseTagTypes(parts[0])
        
        return tag

    """
     Parse tag type string "{Array|Object}" etc.
     
     @param {String} str
     @return {Array}
     @api public
    """

    def parseTagTypes(self, str):
        return re.split('[,|/]', str[1:-1])

    """
     Parse the context from the given `str` of code.
     
     This method attempts to discover the context
     for the comment based on it's code.
     
     @param {String} str
     @return {Object}
     @api public
    """

    def parseCodeContext(self, str):
        str = str.splitlines()[0].strip()

        for k,exp in self.lang.iteritems():
            if k.startswith('comment'):
                continue
            match = re.match(exp, str)
            
            if match != None:
                return {
                    'type' : k,
                    'name' : match.group('name'),
                    'string' : match.group(0),
                }

if __name__ == "__main__":
    import sys
    p = Parser()
    f = open(sys.argv[1])

    for c in p.parseComments(f.read(), 'py'):
        print c['description']['full']+"\n"
        print c['ctx']['string']+"\n\n"

    f.close()
