#! /usr/bin/python

import re, os, os.path

"""
  Parses code and spits out block comments, nicely broken down.

  @see parseComments
"""
class Parser:
    langs = {
        'py' : {
            'class' : r'class (?P<name>[^\(:]+)',
            'function' : r'def (?P<definition>(?P<name>[^\(]+).+):',
            'variable' : r'(?P<name>.+) =',
            'comment_begin' : '"""',
            'comment_middle' : '',
            'comment_end' : '"""',
        },
        'php' : {
            'class' : r'class (?P<name>[^\(\s\{]+)',
            'function' : r'function (?P<definition>(?P<name>[^\(]+).+)',
            'variable' : r'(?P<name>\$.+) =',
            'comment_begin' : '/*',
            'comment_middle' : '*',
            'comment_end' : '*/',
        },
    }

    """
      Parse comments in the given file.

      A code example:

          def echo(s):
            print s
     
      @param {String} file Path of file.
      @return {Array}
      @see parseComments
      @see MarkdownTemplate::renderComments Parser.renderComments
    """
    def parseFile(self, file):
        import os.path
        if os.path.isfile(file):
            (path, ext) = os.path.splitext(file)
            
            if ext[1:] in self.langs:
                self.lang = self.langs[ext[1:]]
                self.filename = os.path.basename(path)
                
                f = open(file)
                comments = self.parseComments(f.read())
                f.close()
                
                return comments
        print "This file type is not supported yet ("+file+")"
        return []
     
    """
      Parse comments in the given code.
     
      @param {String} str String to parse.
      @return {Array}
      @see parseComment
    """
    def parseComments(self, str):
        comments = []
        buf = ''
        ignore = False
        within = False
        
        comment_begin = self.lang['comment_begin']
        comment_end = self.lang['comment_end']
        len_begin = len(comment_begin)
        len_end = len(comment_end)
        whitespace = ['', ' ', '\n', '\t']

        i = 0
        while i < len(str):
            # start comment
            if within == False and str[i:i+len_begin] == comment_begin and (str[i-1] in whitespace):
                # code following previous comment
                if buf.strip() and len(comments) > 0:
                    comment = comments[len(comments) - 1]
                    comment['code'] = buf.strip()
                    comment['ctx'] = self.parseCodeContext(comment['code'])
                buf = ''
                ignore = ('!' == str[i + len_begin])
                i += len_begin + (1 if ignore else 0)
                within = True
            # end comment
            elif within and str[i:i+len_end] == comment_end and (str[i-1] in whitespace):
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
        if len(buf.strip()) and len(comments) > 0:
            comment = comments[len(comments) - 1]
            comment['code'] = buf.strip()
            comment['ctx'] = self.parseCodeContext(comment['code'])

        return comments
    
    """
     Parse the given comment `s`.
     
     The comment object returned contains the following
     
      - `tags`  array of tag objects
      - `description` the first line of the comment
      - `body` lines following the description
      - `content` both the description and the body
      - `isPrivate` True when "@api private" is used
     
     @param {String} s
     @return {Dictionary}
     @see parseTag
     @api public
    """

    def parseComment(self, s):
        comment = {'tags' : []}
        description = {}
        
        # remove the same number of spaces/tabs before each line of the comment (removes indenting)
        spaces = re.match('^\n(\s*)', s).group(1)
        # -- warning --
        # this is a nasty little workaround
        # I couldn't make the line below work:
        #s = re.sub('('+spaces+')', '', s)
        # what's wrong with that? oh well, this works
        # -- end warning --
        lines = ''
        for l in s.split('\n'):
            lines += l.replace(spaces, '', 1)+'\n'
        s = lines.strip()

        # split the description and tags
        pieces = re.split('\s+@', s)

        description['full'] = pieces[0] or s
        # split summary and body (two line breaks, both possibly followed by spaces/tabs
        desc = description['full'].split('\n\n', 1)
        description['summary'] = desc[0]
        description['body'] = ''
        if len(desc) > 1:
            description['body'] = desc[1]

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
     
     @param {String} str
     @return {Dictionary}
     @api public
    """

    def parseTag(self, str):
        parts = str.strip().split(' ')
        tag = {} 
        tag['type'] = parts.pop(0)
        type = tag['type']

        if type == 'param':
            tag['types'] = self.parseTagTypes(parts[0])
            tag['name'] = parts[1] or ''
            tag['description'] = ' '.join(parts[2:] or '')
        elif type == 'return':
            tag['types'] = self.parseTagTypes(parts[0])
            tag['description'] = ' '.join(parts[1:])
        elif type == 'see':
            tag['title'] = parts.pop(0) or ''
            tag['url'] = ' '.join(parts)
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
     @return {Dictionary}
     @api public
    """

    def parseCodeContext(self, str):
        str = str.splitlines()[0].strip()

        for k,exp in self.lang.iteritems():
            if k.startswith('comment'):
                continue
            match = re.search(exp, str)
            
            if match != None:
                ctx = {
                    'type' : k,
                    'name' : match.group('name'),
                    'string' : match.group(0),
                }
                if k == 'function':
                    ctx['definition'] = match.group('definition')

                return ctx
        if self.filename:
            return {'type' : 'file', 'name' : self.filename}

"""
Turns comments into markdown.
"""
class MarkdownTemplate:
    def __init__(self, base_url = ''):
        self.base_url = base_url or ''

    """
        Renders a bunch of comments as markdown.
    """
    def renderComments(self, comments, filename = ''):
        output = ''
        for c in comments:
            if ('isPrivate' in c and c['isPrivate']) or c['ignore']:
                continue
            output += self.renderComment(c, filename)

        return output

    """
        Renders a comment as markdown.

        @api public
    """
    def renderComment(self, comment, filename):
        output = ''

        # class/function header
        output += self._header(comment)
        # function definition
        output += self._definition(comment)
        # description
        output += self._description(comment)

        see = ''
        params = ''
        returns = ''
        for t in comment['tags']:
            type = t['type']

            if type == 'param':
                params += self._param_tag(t)
            elif type == 'return':
                returns += self._return_tag(t)
            elif type == 'see':
                (title, url) = self._see_tag(t)
                see += '['+title+']('+url+')\n\n'
            elif type == 'api':
                #output += 'Visibility: '+t['visibility']+'\n\n'
                pass
            elif type == 'type':
                output += self._see_tag(t)

        if params != '':
            output += self._params(params)
        if returns != '':
            output += self._returns(returns)
        if see != '':
            output += self._see(see)

        return output

    def _header(self, comment):
        type = comment['ctx']['type']
        name = comment['ctx']['name']
        if type == 'class' or type == 'file':
            return "# "+name+"\n\n"
        else:
            return "## "+name+"\n\n"

    def _definition(self, comment):
        if type == 'function':
            return "    "+comment['ctx']['definition']+"\n\n"
        return ''

    def _description(self, comment):
        return comment['description']['full']+"\n\n"

    def _param_tag(self, t):
        return t['name']+' '+'|'.join(t['types'])+' '+t['description']+'\n'
    def _return_tag(self, t):
        return '{'+' | '.join(t['types'])+'}\n\n'+t['description']+'\n\n'
    def _see_tag(self, t):
        url = t['url']
        i = url.rfind('.')
        url = url.replace('.', '/')
        if i > -1:
            url = self.base_url+url[:i]+'#'+url[i+1:]
        return (t['title'], url)
    def _type_tag(self, t):
        return '{'+'|'.join(t['types'])+'}\n\n'

    def _params(self, params):
        return "### Parameters\n\n"+params+"\n"

    def _returns(self, returns):
        return "### Return\n"+returns

    def _see(self, see):
        return "### See\n"+see

class HTMLTemplate(MarkdownTemplate):
    def renderComment(self, comment, filename):
        self.setup_pygment(filename)

        text = MarkdownTemplate.renderComment(self, comment, filename)

        import markdown
        return markdown.markdown(text)

    def setup_pygment(self, filename):
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_for_filename
        
        self.lexer = get_lexer_for_filename(filename)
        self.formatter = HtmlFormatter()

    def _header(self, comment):
        # class/function header
        type = comment['ctx']['type']
        name = comment['ctx']['name']
        if type == 'class' or type == 'file':
            return "# "+name+"\n\n"
        else:
            return "<a name='"+name+"'><h2>"+name+"</a></h2>\n\n"

    def _definition(self, comment):
        # function definition
        if type == 'function':
            return highlight(comment['ctx']['definition'], self.lexer, self.formatter)+"\n\n"
        return ''

    def _description(self, comment):
        from pygments import highlight

        # highlight each line of code
        # insert the highlighted code, replacing the original line of code
        lines = ''
        code = ''
        for l in comment['description']['full'].splitlines():
            if len(l.strip()) > 0 and l.startswith('    '):
                code += l[4:]+'\n'
            elif len(code) > 0:
                lines += highlight(code, self.lexer, self.formatter)+l+'\n'
                code = ''
            else:
                lines += l+'\n'
        if len(code) > 0:
            lines += highlight(code, self.lexer, self.formatter)+'\n'

        return lines+"\n\n"

    def _params(self, params):
        return "### Parameters\n<table>\n"+params+"</table>\n\n"

    def _param_tag(self, t):
        return ' <tr><td>'+t['name']+'</td><td>'+'|'.join(t['types'])+'</td><td>'+t['description']+'</td></tr>\n'
    def _see_tag(self, t):
        url = t['url']
        if url == '':
            url = '#'+t['title']
        else:
            i = url.rfind('.')
            url = url.replace('.', '/')
            if i > -1:
                url = self.base_url+url[:i]+'.html#'+url[i+1:]
            else:
                url = self.base_url+url+'.html'
                
        return (t['title'], url)

class MarcdocTemplate(MarkdownTemplate):
    def renderComment(self, comment, filename):
        return MarkdownTemplate.renderComment(self, comment, filename)

    def _header(self, comment):
        # class/function header
        type = comment['ctx']['type']
        name = comment['ctx']['name']
        if type == 'class' or type == 'file':
            return "# "+name+"\n\n"
        else:
            return "<a name='"+name+"'><h2>"+name+"</a></h2>\n\n"

class Renderer:
    def __init__(self, output_type, base_url = ''):
        self.parser = Parser()
        self.output_html = (output_type == 'html')

        if output_type == 'html':
            self.template = HTMLTemplate(base_url)
        elif output_type == 'marcdoc':
            self.template = MarcdocTemplate(base_url)
        else:
            self.template = MarkdownTemplate(base_url)

    def renderFile(self, file, out_file):
        comments = self.parser.parseFile(file)

        if len(comments) > 0:
            text = self.template.renderComments(comments, file)

            (path, ext) = os.path.splitext(out_file)
            if self.output_html:
                out_file = path+'.html'
            else:
                out_file = path+'.md'

            f = open(out_file, "w+")
            f.write(text)
            f.close()

    def renderDirectory(self, dir, out_dir):
        for f in os.listdir(dir):
            # skip dot files
            if f[0] == '.':
                continue

            out = out_dir+'/'+f
            f = dir+'/'+f

            if os.path.isfile(f):
                self.renderFile(f, out)
            elif os.path.isdir(f):
                self.renderDirectory(f, out)

if __name__ == "__main__":
    def opt_parser():
        from optparse import OptionParser
        parser = OptionParser("usage: %prog [options] file1 [file2...]")

        parser.add_option("-d", "--directory", dest="directory", help="writes file(s) to DIR", metavar="DIR", default=".")
        parser.add_option("-o", "--output", dest="output", help="outputs files as one of: html, marcdoc, markdown", default='markdown')
        parser.add_option("-b", "--base-url", dest="base_url", help="base url for links")

        return parser

    opt_parser = opt_parser()
    (options, args) = opt_parser.parse_args()

    if len(args) < 1:
        opt_parser.error("Need at least one file to parse.")

    renderer = Renderer(options.output, options.base_url)

    for f in args:
        out = options.directory+'/'+os.path.basename(f)
        if os.path.isfile(f):
            renderer.renderFile(f, out)
        elif os.path.isdir(f):
            renderer.renderDirectory(f, out)
