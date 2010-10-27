import os
import sys
import json
from urllib2 import urlopen

from BeautifulSoup import BeautifulSoup
from html2text import html2text


def parse(issue_html):
    soup = BeautifulSoup(issue_html)

    status = None
    for v in soup.findAll('td', 'val'): 
        cl = v['class']
        class_vals = cl.split()
        for class_val in class_vals:
            if class_val.lower().startswith('issue-status-'):
                status = class_val.lower()[len('issue-status-'):]
                break

    comments = soup.findAll('li', 'comment-content')
    comments_data = []
    for i, comment in enumerate(comments):
        author_name_tag = comment.find('img').findNextSibling('a')
        author_name = author_name_tag.text if author_name_tag else None 
        author_username_tag = (author_name_tag.findNextSibling('a') 
                               if author_name_tag else None)
        author_username = (author_username_tag.text if author_username_tag else None)

        if (author_username is None and author_name is not None):
            author_username, author_name = author_name, author_username
        timestamp = comment.find('abbr', 'timeago')['title']
        div = comment.find('div', 'issues-comment')
        markdown_text = html2text(unicode(div)) if div else None
        comment_data = dict(index=i,
                            author_name=author_name,
                            author_username=author_username,
                            timestamp=timestamp,
                            markdown_text=markdown_text)
        comments_data.append(comment_data)
    return status, comments_data


def add_comments(issues):
    for issue in issues:
        resource_uri = issue['resource_uri']
        uri_parts = resource_uri.split('/')
        repo_owner = uri_parts[3]
        repo_name = uri_parts[4]
        issue_id = issue['local_id']
        url = ('http://bitbucket.org/'
               '%(repo_owner)s/%(repo_name)s'
               '/issue/%(issue_id)s' % locals())
        fname = resource_uri.replace('/', '_')
        if (os.path.exists(fname)):
            with open(fname) as f:
                issue_html = f.read()
        else:
            issue_html = urlopen(url).read()
            with open(fname, 'w') as f:
                f.write(issue_html)

        status, comments = parse(issue_html)
        issue['status'] = status
        issue['comments'] = comments
    return issues


if __name__ == '__main__':
    issues_fname = sys.argv[1]

    with open(issues_fname) as issues_file:
        issues_data = json.load(issues_file)

    issues_with_comments = add_comments(issues_data['issues'])
    sys.stdout.write(json.dumps(issues_with_comments, indent=2))

