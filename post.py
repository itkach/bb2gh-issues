import sys
import json
from datetime import datetime

from github2.client import Github

if __name__ == '__main__':
    username = sys.argv[1]
    api_token = sys.argv[2]
    project = sys.argv[3]
    issues_fname = sys.argv[4]
    gh2 = Github(username=username, api_token=api_token)

    with open(issues_fname) as f:
        issues = json.load(f)

    for issue in sorted(issues, key=lambda x: x['local_id']):
        title = issue['title']
        print 'Exporting issue #%d' % issue['local_id'] 
        body = issue['content']
        reported_by = issue.get('reported_by', {})
        reported_by_user = reported_by.get('username', 'anonymous')
        status = issue['status']
        created_on = issue['created_on'].split()[0]
        created_on = datetime.strptime(created_on, '%Y-%m-%d').strftime('%b %d, %Y')

        info = (u'_(Originally reported by %s on %s at BitBucket)_'
                % (reported_by_user, created_on))
        body = u'%s\n\n%s' % (info, body)

        gh_issue = gh2.issues.open(project, title, body)

        metadata = issue['metadata']

        for comment in issue['comments']:
            content = comment['markdown_text']
            if not content:
                continue
            timestamp = comment['timestamp']
            commented_on = (datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
                            .strftime('%b %d, %Y'))
            commented_by = comment.get('author_username') or 'anonymous'
            comment_info = (u'_(Commented by %s on %s at BitBucket)_' %
                            (commented_by, commented_on))
            comment_body = u'%s\n\n%s' % (comment_info, content)
            print 'Exporting comment #%d' % comment['index']
            gh2.issues.comment(project, gh_issue.number, comment_body)


        kind = metadata.get('kind')
        if kind == 'enhancement' or kind == 'proposal':
            gh2.issues.add_label(project, 
                                 gh_issue.number, 
                                 'enhancement')

        if status == 'resolved':
            if 'version' in metadata:
                ver = metadata['version']
                if ver:
                    gh2.issues.comment(project, gh_issue.number,
                                       'Resolved in %s' % ver)
            gh2.issues.close(project, gh_issue.number)
        elif status == 'wontfix':
            gh2.issues.add_label(project, gh_issue.number, 'wontfix')
            gh2.issues.close(project, gh_issue.number)            
        elif status == 'invalid':
            gh2.issues.add_label(project, gh_issue.number, 'invalid')
            gh2.issues.close(project, gh_issue.number)
        elif status == 'onhold':
            gh2.issues.add_label(project, gh_issue.number, 'onhold')
        elif status == 'new' or status == 'open':
            if 'version' in metadata:
                ver = metadata['version']
                if ver:
                    gh2.issues.comment(project, gh_issue.number,
                                       'Affects %s' % ver)

