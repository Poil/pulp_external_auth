* Apache Configuration :
  * Install Module

```
yum install  mod_authnz_external
```

  * /etc/httpd/conf.d/authnz_external.conf

```
LoadModule authnz_external_module modules/mod_authnz_external.so
DefineExternalAuth pwauth pipe /usr/bin/pwauth
DefineExternalAuth ldapssa pipe /usr/local/bin/auth_ldap.py
```

  * /etc/httpd/conf.d/pulp.conf

```
<Files webservices.wsgi>
    # pass everything that isn't a Basic auth request through to Pulp
    SetEnvIfNoCase ^Authorization$ "Basic.*" USE_APACHE_AUTH=1
    Require env !USE_APACHE_AUTH

    ## configure external LDAP auth
    AuthType Basic
    AuthName "Pulp"
    AuthBasicProvider external
    AuthExternal ldapssa
    Require valid-user
    # Standard Pulp REST API configuration goes here...
    WSGIPassAuthorization On
    WSGIProcessGroup pulp
    WSGIApplicationGroup pulp
    SSLRenegBufferSize  1048576
    SSLRequireSSL
    SSLVerifyDepth 3
    SSLOptions +StdEnvVars +ExportCertData
    SSLVerifyClient optional
</Files>
``` 

* Configuration file : auth_ldap.yaml
  * Path : /usr/local/etc/auth_ldap.yaml
  * Mode : 0700
  * Owner : apache

* LDAP account
  * Account will be automatically created in Pulp local DB if LDAP authentication succeeded
  * Add memberOf in the role you want in the role_mapping configuration

* Service account
```
pulp-admin auth role create --role-id api
pulp-admin auth permission grant --role-id=api --resource="/v2/content/uploads/" -o read -o update -o create -o delete
pulp-admin auth permission grant --role-id=api --resource="/v2/tasks/" -o read
...
pulp-admin auth user create --login team2
pulp-admin auth role user add --login team2 --role-id api
```
