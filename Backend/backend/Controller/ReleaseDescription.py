"""Convert release Markdown to readable plain text for AtronUpdate."""
from html.parser import HTMLParser

import markdown


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.lists = []
        self.links = []
        self.hidden = 0
        self.pre = False

    def newline(self):
        if self.parts and not self.parts[-1].endswith('\n'):
            self.parts.append('\n')

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style'):
            self.hidden += 1
        if self.hidden:
            return
        if tag in ('p', 'div', 'blockquote', 'pre', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.newline()
        if tag in ('ul', 'ol'):
            self.newline()
            self.lists.append([tag, int(attrs.get('start', '1'))])
        elif tag == 'li':
            self.newline()
            marker = '- '
            if self.lists and self.lists[-1][0] == 'ol':
                marker = str(self.lists[-1][1]) + '. '
                self.lists[-1][1] += 1
            self.parts.append('  ' * max(0, len(self.lists) - 1) + marker)
        elif tag in ('br', 'hr'):
            self.newline()
        elif tag == 'a':
            self.links.append((attrs.get('href', ''), len(self.parts)))
        elif tag == 'img':
            self.parts.append(attrs.get('alt', ''))
        elif tag == 'pre':
            self.pre = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.hidden:
            self.hidden -= 1
            return
        if self.hidden:
            return
        if tag == 'a' and self.links:
            url, start = self.links.pop()
            if url and url != ''.join(self.parts[start:]):
                self.parts.append(' (' + url + ')')
        if tag in ('ul', 'ol') and self.lists:
            self.lists.pop()
        if tag in ('td', 'th'):
            self.parts.append('\t')
        if tag in ('p', 'div', 'blockquote', 'pre', 'tr', 'li', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.newline()
        if tag in ('p', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.parts.append('\n')
        if tag == 'pre':
            self.pre = False

    def handle_data(self, data):
        if not self.hidden and (self.pre or data.strip()):
            self.parts.append(data)
        elif not self.hidden and data == ' ':
            self.parts.append(data)


def release_description(body):
    parser = _PlainText()
    parser.feed(markdown.markdown(body, extensions=['fenced_code', 'tables', 'sane_lists']))
    parser.close()
    return ''.join(parser.parts).strip()
