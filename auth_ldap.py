#!/usr/bin/env python

import sys
import subprocess
import yaml
import ldap

if __name__ == "__main__":
    try:
        with open("/usr/local/etc/auth_ldap.yaml", 'r') as stream:
            config = yaml.load(stream)
    except yaml.YAMLError:
        sys.stderr.write("Wrong yaml file\n")
        sys.exit(1)
    except EnvironmentError:
        sys.stderr.write("Can\'t read /usr/local/etc/auth_ldap.yaml\n")
        sys.exit(1)

    super_admin = config['super_admin']
    super_password = config['super_password']

    user_name = sys.stdin.readline().strip()
    user_password = sys.stdin.readline().strip()

    if user_name == config['super_admin'] and user_password == config['super_password']:
        sys.stderr.write("Super admin is authenticated\n")
        sys.exit(0)

    if user_name in config['service_account'] and user_password == config['service_account'][user_name]:
        sys.stderr.write("Service account is authenticated\n")
        sys.exit(0)

    ldap.set_option(ldap.OPT_REFERRALS, 0)
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    ldap.protocol_version = 3
    # ldap.set_option(ldap.OPT_DEBUG_LEVEL, 999999)

    ldap_server = config['ldap_server']
    # the following is the user_dn format provided by the ldap server
    service_user_dn = config['service_user_dn']
    service_user_password = config['service_user_password']
    # adjust this to your base dn for searching
    base_dn = config['base_dn']
    connect = ldap.initialize(ldap_server)
    search_filter = "uid={}".format(user_name)
    try:
        # if authentication successful, get the full user data
        connect.bind_s(service_user_dn, service_user_password)
        result = connect.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)

        if len(result) > 1:
            sys.stderr.write("Authentication failed: multiple match for user {} in the LDAP Tree\n".format(user_name))
            sys.exit(1)
        sys.stderr.write("Result {}\n".format(result))

        user_dn = result[0][0]
        member_of = result[0][1]['memberOf']
        sys.stderr.write("Found user_dn {}\n".format(user_dn))
        sys.stderr.write("Found memberOf {}\n".format(member_of))
        connect.unbind_s()

        # try to bind with founded user_dn / passed password
        try:
            connectu = ldap.initialize(ldap_server)
            connectu.bind_s(user_dn, user_password)
            sys.stderr.write("Check {}\n".format(connectu.whoami_s()))
            sys.stderr.write("Authentication OK: for user {} {}\n".format(user_name, user_dn))
            connectu.unbind_s()
            # Check if user already exist in the local DB
            r = subprocess.check_output([
                '/usr/bin/pulp-admin',
                '-u', super_admin,
                '-p', super_password,
                'auth', 'user', 'search',
                '--fields=login',
                '--str-eq=login={}'.format(user_name)])

            # If not create it and bind it to his role
            if user_name not in r:
                sys.stderr.write("User {} does not exist in pulpDB\n".format(user_name))
                subprocess.call([
                    '/usr/bin/pulp-admin',
                    '-u', super_admin,
                    '-p', super_password,
                    'auth', 'user', 'create',
                    '--login={}'.format(user_name),
                    '--password={}'.format(user_password)])

                for role in config['role_mapping']:
                    for group in role:
                        if group in member_of:
                            subprocess.call([
                                '/usr/bin/pulp-admin',
                                '-u', super_admin,
                                '-p', super_password,
                                'auth', 'role', 'user', 'add',
                                '--login={}'.format(user_name),
                                '--role-id={}'.format(role)])
            else:
                sys.stderr.write("User {} already exists in pulpDB\n".format(user_name))
            sys.stderr.write("Authentication successful for user {}\n".format(user_name))
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            sys.stderr.write("pulp-admin failed with error {}\n".format(e))
            connectu.unbind_s()
            sys.exit(1)
        except ldap.INVALID_CREDENTIALS:
            sys.stderr.write("Authentication failed: wrong password or username for user {} with full_dn {}\n".format(
                user_name, user_dn))
            connectu.unbind_s()
            sys.exit(1)
        except ldap.SERVER_DOWN:
            sys.stderr.write("LDAP server {} is unavailable\n".format(ldap_server))
            connectu.unbind_s()
            sys.exit(1)
        except ldap.LDAPError:
            sys.stderr.write("Unkown LDAP Service Authentication error\n")
            connectu.unbind_s()
            sys.exit(1)
        except Exception as e:
            sys.stderr.write("Unknown other error %s" % e)
            sys.exit(1)

    except ldap.INVALID_CREDENTIALS:
        sys.stderr.write("Service Authentication failed: wrong password or username for user {}\n".format(
            service_user_dn))
        connect.unbind_s()
        sys.exit(1)
    except ldap.SERVER_DOWN:
        sys.stderr.write("LDAP server {} is unavailable\n".format(ldap_server))
        connect.unbind_s()
        sys.exit(1)
    except ldap.LDAPError:
        sys.stderr.write("Unkown LDAP Service Authentication error\n")
        connect.unbind_s()
        sys.exit(1)
    except Exception as e:
        sys.stderr.write("Unknown other error %s" % e)
        sys.exit(1)
