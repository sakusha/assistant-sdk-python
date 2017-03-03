#
# Copyright (C) 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""auth_helpers implements Device and Web authorization flow."""

import json
import logging

import google.auth.transport.requests
import google.oauth2.flow
import google.oauth2.credentials
import grpc
import six.moves


def credentials_flow_interactive(client_secrets_file, scopes):
    """Initiate an interactive OAuth2InstalledApp flow.

    - Display a URL for the user to visit.
    - URL displays a code for the user to copy.
    - Wait on standard input for the user to enter the provided code.
    - Exchange OAuth2 tokens.
    - Returns credentials.

    Args:
      client_secrets_file: The path to the client secrets JSON file.
      scopes: The list of scopes to request during the flow.
    Returns:
      google.oauth2.credentials.Credentials: new OAuth2 credentials authorized
        with the given scopes.
    """
    flow = google.oauth2.flow.Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=scopes,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    auth_url, _ = flow.authorization_url(prompt='consent')
    print('Please go to this URL: %s' % auth_url)
    code = six.moves.input('Enter the authorization code: ')
    flow.fetch_token(code=code)
    return flow.credentials


def credentials_to_dict(credentials):
    return {'access_token': credentials.token,
            'refresh_token': credentials._refresh_token,
            'token_uri': credentials._token_uri,
            'client_id': credentials._client_id,
            'client_secret': credentials._client_secret}


def credentials_from_dict(credentials, scopes):
    return google.oauth2.credentials.Credentials(
        credentials['access_token'],
        credentials['refresh_token'],
        credentials['token_uri'],
        credentials['client_id'],
        credentials['client_secret'],
        scopes=scopes)


def save_credentials(path, credentials):
    """Write credentials to the given file.
    Args:
      path(str): path to the credentials file.
      credentials(google.oauth2.credentials.Credentials): OAuth2 credentials.
    """
    with open(path, 'w') as f:
        json.dump(credentials_to_dict(credentials), f)


def load_credentials(path, scopes):
    """Load credentials from the given file.
    Args:
      path(str): path to the credentials file.
      scopes: scope for the given credentials.
    Returns:
      google.oauth2.credentials.Credentials: OAuth2 credentials.
    """
    with open(path, 'r') as f:
        return credentials_from_dict(json.load(f),
                                     scopes=scopes)


def create_grpc_channel(target, credentials, ssl_credentials_file=None,
                        grpc_channel_options=None):
    """Create and return a gRPC channel.

    Args:
      credentials(google.oauth2.credentials.Credentials): OAuth2 credentials.
      ssl_credentials_file(str): Path to SSL credentials.pem file (for testing).
      grpc_channel_options([(option_name, option_val)]): gRPC channel options.
    Returns:
      grpc.Channel.
    """
    ssl_credentials = None
    if ssl_credentials_file:
        with open(ssl_credentials_file) as f:
            ssl_credentials = grpc.ssl_channel_credentials(f.read())
    http_request = google.auth.transport.requests.Request()
    return google.auth.transport.grpc.secure_authorized_channel(
        credentials, http_request, target,
        ssl_credentials=ssl_credentials, options=grpc_channel_options or [])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='helper script '
                                     'to generate OAuth2 credentials')
    parser.add_argument('client_secrets', type=str,
                        help='Path to OAuth2 client secret JSON file. ')
    parser.add_argument('scopes', type=str, nargs='+',
                        help='API scopes to authorize access for.')
    args = parser.parse_args()
    credentials = credentials_flow_interactive(args.client_secrets,
                                               args.scopes)
    logging.info('access_token: %s' % credentials['access_token'])