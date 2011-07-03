#! /usr/bin/python

import re

class Parser:
    langs = {
        'py' : {
            'class' : 'class ([^\(]+)',
            'function' : 'def (.+):',
            'comment_begin' : '"""',
            'comment_end' : '"""',
        },
        'php' : {
            'class' : 'class ([^\(]+)',
            'function' : 'function (.+):',
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
    def parseComments(self, str):
        comments = []
        comment = {}
        buf = ''
        ignore = false
        within = false
        code = ''

        comment_begin = self.lang['comment_begin']
        comment_end = self.lang['comment_end']

        for i in range(0, len(str)):
            # start comment
            if !within && str[i:i+len(comment_begin)] == comment_begin:
                # code following previous comment
                if buf.strip():
                    comment = comments[len(comments) - 1]
                    comment['code'] = code = buf.strip()
                    comment['ctx'] = self.parseCodeContext(code)
                    buf = ''
                }
                i += 2
                within = true
                ignore = ('!' == str[i + len(comment_begin) + 1])
            # end comment
            elif within && str[i:i+len(comment_end)] == comment_end:
                i += 2
                buf = re.replace('^\s*'+re.escape(self.lang['comment_middle'])+' ?', '')
                comment = self.parseComment(buf)
                comment['ignore'] = ignore
                comments.append(comment)

                within = false
                ignore = false
                buf = ''
            # buffer comment or code
            else:
                buf += str[i]
        
        # trailing code
        if len(buf.strip()):
            comment = comments[len(comments) - 1]
            code = buf.strip()
            comment['code'] = code
            comment['ctx'] = self.parseCodeContext(code)
        }

        return comments
    
    """
     Parse the given comment `str`.
     
     The comment object returned contains the following
     
      - `tags`  array of tag objects
      - `description` the first line of the comment
      - `body` lines following the description
      - `content` both the description and the body
      - `isPrivate` true when "@api private" is used
     
     @param {String} str
     @return {Object}
     @see exports.parseTag
     @api public
    """

    def parseComment(self, str):
        str = str.strip()
        comment = { tags: [] }
        description = {}
        
        # parse comment body
        description['full'] = str.split('\n@')[0]
        
        desc = description['full'].split('\n\n')
        description['summary'] = desc[0]
        description['body'] = (len(desc) > 1) ? '\n\n'.join(desc.split('\n\n')[1:]) : ''
        comment['description'] = description
        
        # parse tags
        if str.find('\n@'):
            #tags = '@' + '\n@'.join(str.split('\n@'))
            comment['tags'] = map(self.parseTag, tags.splitlines())
            for t in comment['tags']:
                if t['type'] == 'api' && tag['visibility'] == 'private':
                    comment['isPrivate'] = true
                    break
        
        return comment
    
    """
     Parse tag string "@param {Array} name description" etc.
     
     @param {String}
     @return {Object}
     @api public
    """

    def parseTag(self, str):
        parts = str.split(' ')
        tag = {} 
        tag['type'] = parts.pop(0)[1:]
        type = tag['type']

        if type == 'param':
            tag['types'] = self.parseTagTypes(parts[1:])
            tag['name'] = parts[2:] or ''
            tag['description'] = ' '.join(parts[3:] or '')
        elif type == 'return':
            tag['types'] = self.parseTagTypes(parts[1:])
            tag['description'] = ' '.join(parts[2:])
        elif type == 'see':
            if str.find('http'):
                tag['title'] = len(parts) > 1 ? parts.pop(0) : ''
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

        for k,exp in self.lang:
            if k.startswith('comment'):
                continue
            match = re.match(exp, str)
            
            if match != None:
                return {
                    'name' : match.group('name'),
                    'string' : match.group(0),
                }

if __name__ == "__main__":
    import sys
    p = Parser
    f = open(sys.argv[1])

    print p.parseComments(f.read())

    f.close()
