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
        print "This file type is not supported yet.\n"
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
                i += len_begin
                within = True
                ignore = ('!' == str[i + len_begin + 1])
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
        if len(buf.strip()):
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

class Template:
    def __init__(self, base_url = ''):
        self.base_url = base_url or ''

    """
        Renders a bunch of comments as markdown.
    """
    def renderComments(self, comments, filename = ''):
        output = ''
        for c in comments:
            if 'isPrivate' in c and c['isPrivate']:
                continue
            output += self.renderComment(c, filename)

        return output

    def renderComment(self, comment, filename):
        pass
"""
Turns comments into markdown.
"""
class MarkdownTemplate(Template):
    """
        Renders a comment as markdown.

        @api private
    """
    def renderComment(self, comment, filename):
        output = ''

        # class/function header
        type = comment['ctx']['type']
        name = comment['ctx']['name']
        if type == 'class' or type == 'file':
            output += "# "+name+"\n\n"
        else:
            output += "## "+name+"\n\n"
        # function definition
        if type == 'function':
            output += "    "+comment['ctx']['definition']+"\n\n"
        # description
        output += comment['description']['full']+"\n\n"

        see = ''
        params = ''
        returns = ''
        for t in comment['tags']:
            type = t['type']

            if type == 'param':
                params += t['name']+' '+'|'.join(t['types'])+' '+t['description']+'\n'
            elif type == 'return':
                returns += ' '.join(t['types'])+' '+t['description']+'\n\n'
            elif type == 'see':
                url = t['url']
                i = url.rfind('.')
                url = url.replace('.', '/')
                if i > -1:
                    url = self.base_url+url[:i]+'#'+url[i+1:]
                see += '['+t['title']+']('+url+')\n\n'
            elif type == 'api':
                #output += 'Visibility: '+t['visibility']+'\n\n'
                pass
            elif type == 'type':
                output += ' '.join(t['types'])+'\n\n'

        if params != '':
            output += "### Parameters\n\n"+params+"\n"
        if returns != '':
            output += "### Returns\n"+returns
        if see != '':
            output += "### See\n"+see

        return output

class HTMLTemplate(Template):
    def setup_pygment(self, filename):
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_for_filename
        
        self.lexer = get_lexer_for_filename(filename)
        self.formatter = HtmlFormatter()

    def renderComment(self, comment, filename):
        from pygments import highlight

        self.setup_pygment(filename)

        output = ''

        # class/function header
        type = comment['ctx']['type']
        name = comment['ctx']['name']
        if type == 'class' or type == 'file':
            output += "# "+name+"\n\n"
        else:
            output += "<a name='"+name+"'><h2>"+name+"</a></h2>\n\n"
        # function definition
        if type == 'function':
            output += highlight(comment['ctx']['definition'], self.lexer, self.formatter)+"\n\n"

        # description
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

        output += lines+"\n\n"

        see = ''
        params = ''
        returns = ''
        for t in comment['tags']:
            type = t['type']

            if type == 'param':
                params += ' <tr><td>'+t['name']+'</td><td>'+'|'.join(t['types'])+'</td><td>'+t['description']+'</td></tr>\n'
            elif type == 'return':
                returns += ' '.join(t['types'])+' '+t['description']+'\n\n'
            elif type == 'see':
                url = t['url']
                if url == '':
                    url = '#'+t['title']
                else:
                    i = url.rfind('.')
                    url = url.replace('.', '/')
                    if i > -1:
                        url = self.base_url+url[:i]+'.html#'+url[i+1:]
                see += '['+t['title']+']('+url+')\n\n'
            elif type == 'api':
                #output += 'Visibility: '+t['visibility']+'\n\n'
                pass
            elif type == 'type':
                output += ' '.join(t['types'])+'\n\n'

        if params != '':
            output += "### Parameters\n<table>\n"+params+"</table>\n\n"
        if returns != '':
            output += "### Returns\n"+returns
        if see != '':
            output += "### See\n"+see

        import markdown
        return markdown.markdown(output)


class Renderer:
    def __init__(self, output_html = False, base_url = ''):
        self.parser = Parser()
        self.template = HTMLTemplate(base_url) if output_html else MarkdownTemplate(base_url)
        self.output_html = output_html

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
            f = dir+'/'+f
            out = out_dir+'/'+f
            if os.path.isfile(f):
                self.renderFile(f, out)
            elif os.path.isdir(f):
                self.renderDirectory(f, out)

if __name__ == "__main__":
    def opt_parser():
        from optparse import OptionParser
        parser = OptionParser("usage: %prog [options] file1 [file2...]")

        parser.add_option("-d", "--directory", dest="directory", help="writes file(s) to DIR", metavar="DIR", default=".")
        parser.add_option("", "--html", action="store_true", dest="html", help="outputs files as html", default=False)
        parser.add_option("-b", "--base-url", dest="base_url", help="base url for links")

        return parser

    opt_parser = opt_parser()
    (options, args) = opt_parser.parse_args()

    if len(args) < 1:
        opt_parser.error("Need at least one file to parse.")

    renderer = Renderer(options.html, options.base_url)

    for f in args:
        out = options.directory+'/'+f
        if os.path.isfile(f):
            renderer.renderFile(f, out)
        elif os.path.isdir(f):
            renderer.renderDirectory(f, out)
