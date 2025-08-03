from guardian.core import ObjectPermissionChecker
from rest_framework.status import HTTP_403_FORBIDDEN
from rest_framework.response import Response
from .models import Cart


def cart_obj_permission_required(view_func):
    def _wrapper(request,*args, **kwargs):
        pk = kwargs.get("pk")
        obj = Cart.objects.get(pk=pk)

        user = request.request.user
        checker = ObjectPermissionChecker(user_or_group=user)

        if checker.has_perm(perm="carts.view_cart",obj=obj) or \
            checker.has_perm(perm="carts.delete_cart",obj=obj):

            return Response({"detail": "Permission denied"},status=HTTP_403_FORBIDDEN)
        return view_func(request,*args, **kwargs)
    return _wrapper