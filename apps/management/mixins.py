from django.contrib.auth.mixins import UserPassesTestMixin
from apps.core.models import UserRoles


class RoleTestMixin(UserPassesTestMixin):
    roles = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            #    redirect to default login_url
            return False
        
        if not self.request.user.role in self.roles:
            self.login_url = 'not_authorized'
            return False
        
        return True
        

class ManagerTestMixin(RoleTestMixin):
    roles = [UserRoles.ADMINISTRATOR, UserRoles.MANAGER, UserRoles.OWNER]


class AdminTestMixin(RoleTestMixin):
    roles = [UserRoles.ADMINISTRATOR]
    

class OwnerTestMixin(RoleTestMixin):
    roles = [UserRoles.ADMINISTRATOR, UserRoles.OWNER]

