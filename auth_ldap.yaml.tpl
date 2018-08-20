ldap_server: "ldaps://127.0.0.1"

service_user_dn: "uid=team2,ou=client,o=level3,dc=france,dc=com"
service_user_password: yyyyyyxxxxxxx

base_dn: "dc=france,dc=com"

super_admin: admin
super_password: xxxxxxxxxxxx

service_account:
  team2: yyyyyyyyyyy


role_mapping:
  super_admin:
    - 'cn=admin,ou=group,o=level3,dc=france,dc=com'

