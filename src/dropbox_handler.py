import sys
import os
import json
from AppKit import NSPasteboard, NSArray
import webbrowser
from workflow import Workflow, PasswordNotFound
from dropbox import client, rest
import config


def main(wf):
    user_input = ''.join(wf.args)

    command = user_input.split()[0]
    query = user_input[len(command) + 1:]
    access_token = uid = path = ''
    if len(query.split()) > 0:
        uid = query.split()[0]
        path = query[len(uid) + 1:]
        try:
            access_tokens = json.loads(
                wf.get_password('dropbox_access_tokens'))
            if uid in access_tokens:
                access_token = access_tokens[uid]
        except PasswordNotFound:
            pass

    if access_token != '' and command == "share":
        return share_path(path, access_token)
    elif access_token != '' and command == "download":
        return download_path(path, access_token)
    elif access_token != '' and command == "desktop":
        return download_path(path, access_token, '~/Desktop/')
    elif access_token != '' and command == "delete":
        return delete_path(path, access_token)
    elif command == "url":
        webbrowser.open(query)
        return 0
    elif command == "auth":
        return authorize(query)
    elif command == "remove":
        return remove(query)

    print 'An error occured.'
    return 0


def share_path(path, access_token):
    api_client = client.DropboxClient(access_token)
    try:
        url = api_client.share(path)['url']

        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        a = NSArray.arrayWithObject_(url)
        pb.writeObjects_(a)

        print 'Link copied to clipboard'

    except rest.ErrorResponse, e:
        print e.user_error_msg or str(e)

    return 0


def download_path(path, access_token, target='~/Downloads/'):
    api_client = client.DropboxClient(access_token)
    try:
        filename = os.path.basename(path)
        to_file_path = os.path.expanduser('%s%s' % (target, filename))
        i = 1
        while os.path.isfile(to_file_path):
            (root, ext) = os.path.splitext(filename)
            to_file_path = os.path.expanduser(
                '%s%s%s%s' % (target, root, '-' + str(i), ext))
            i += 1

        to_file = open(to_file_path, "wb")

        f, metadata = api_client.get_file_and_metadata(path)
        to_file.write(f.read())

        os.popen('open -R "%s"' % to_file_path)

        print '%s saved to %s' % (filename, target)

    except rest.ErrorResponse, e:
        print e.user_error_msg or str(e)

    return 0


def delete_path(path, access_token):
    api_client = client.DropboxClient(access_token)
    try:
        self.api_client.file_delete(path)
        print 'File deleted successfully'
    except rest.ErrorResponse, e:
        print e.user_error_msg or str(e)

    return 0


def authorize(auth_code):
    flow = client.DropboxOAuth2FlowNoRedirect(
        config.APP_KEY, config.APP_SECRET)
    try:
        access_token, user_id = flow.finish(auth_code)

        access_tokens = {}
        try:
            access_tokens = json.loads(
                wf.get_password('dropbox_access_tokens'))
        except PasswordNotFound:
            pass

        access_tokens[user_id] = access_token
        wf.save_password('dropbox_access_tokens', json.dumps(access_tokens))
        wf.clear_cache()
        print 'Authorization successful'
    except rest.ErrorResponse, e:
        print 'Error: %s' % (e,)

    return 0


def remove(uid):
    try:
        access_tokens = json.loads(wf.get_password('dropbox_access_tokens'))
        access_token = access_tokens.pop(uid, None)
        api_client = client.DropboxClient(access_token)
        api_client.disable_access_token()
        wf.save_password('dropbox_access_tokens', json.dumps(access_tokens))
        wf.clear_cache()
        print 'Deauthorization successful'
    except PasswordNotFound:
        print 'Not access tokens found.'

    return 0


if __name__ == '__main__':
    wf = Workflow()
    sys.exit(wf.run(main))
