from ldap3 import *

def authenticate(username,password):
        POST_USERNAME = username
        POST_PASSWORD = password

        server = Server('ldap://bluepages.ibm.com', get_info=ALL)
        c = Connection(server, user="", password="", raise_exceptions=False)
        noUseBool = c.bind()

        checkUserIBM = c.search(search_base='ou=bluepages,o=ibm.com',
                                search_filter='(mail=%s)' % (POST_USERNAME),
                                search_scope=SUBTREE,
                                attributes=['dn', 'givenName'])

        if (checkUserIBM == False):
            return False,"NoUser"

        # get the username of the emailID and authenticate password
        userName = c.entries[0].givenName[0]
        uniqueID = c.response[0]['dn']
        c2 = Connection(server, uniqueID, POST_PASSWORD)
        isPassword = c2.bind()

        if (isPassword == False):
            return False,"NoUser"

        # now search group
        checkIfAdminGroup = c.search(search_base='cn=RSC_B2B,ou=memberlist,ou=ibmgroups,o=ibm.com',
                                     search_filter='(uniquemember=%s)' % (str(uniqueID)),
                                     search_scope=SUBTREE,
                                     attributes=['dn'])

        if (checkIfAdminGroup == False):
            return False,"NoUser"

        #all cases correct then authenticate him
        return True,userName